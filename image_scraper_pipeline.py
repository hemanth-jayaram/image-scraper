#!/usr/bin/env python3
"""
Article Image Scraper Pipeline

This script processes JSON files containing article metadata and scrapes
relevant images from the article URLs using a multi-fallback approach.

Author: AI Assistant
Requirements: See requirements.txt
"""

import os
import json
import re
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Third-party libraries for web scraping
import trafilatura
import trafilatura.metadata
from newspaper import Article
from bs4 import BeautifulSoup
from PIL import Image
import io


class ImageScraperPipeline:
    """
    A comprehensive pipeline for scraping article images from JSON metadata files.
    
    Uses a fallback chain: trafilatura -> newspaper3k -> BeautifulSoup
    """
    
    def __init__(self, input_folder: str = ".", output_folder: str = "articles+images"):
        """
        Initialize the scraper pipeline.
        
        Args:
            input_folder: Folder containing JSON files with article metadata
            output_folder: Output folder for organized articles and images
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.session = self._create_session()
        self.logger = self._setup_logging()
        
        # Create output directory
        self.output_folder.mkdir(exist_ok=True)
        
        # Image filtering settings
        self.min_image_size = (100, 100)  # Minimum width x height
        self.max_file_size_mb = 10  # Maximum file size in MB
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        self.max_images_per_article = 1  # Only download the most relevant image per article
        
        # Common patterns to exclude (ads, logos, icons, tracking pixels)
        self.exclude_patterns = [
            r'logo', r'icon', r'favicon', r'avatar', r'profile',
            r'advertisement', r'ad[_-]', r'banner', r'widget',
            r'social', r'share', r'button', r'arrow', r'play',
            r'thumbnail.*small', r'thumb.*\d+x\d+', r'\d+x\d+.*thumb',
            # Tracking pixels and analytics
            r'facebook\.com/tr', r'google-analytics', r'googletagmanager',
            r'doubleclick', r'googlesyndication', r'adsystem',
            r'pixel\?', r'track\?', r'beacon\?', r'analytics',
            r'1x1\.gif', r'transparent\.gif', r'spacer\.gif'
        ]
        self.exclude_regex = re.compile('|'.join(self.exclude_patterns), re.IGNORECASE)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy and proper headers."""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set user agent to avoid blocking
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        return session

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string to be safe for use as a filename.
        
        Args:
            filename: Raw filename string
            
        Returns:
            Sanitized filename safe for filesystem use
        """
        # Remove/replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove extra whitespace and limit length
        filename = re.sub(r'\s+', ' ', filename.strip())[:100]
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        return filename if filename else "unnamed_article"

    def extract_images_trafilatura(self, url: str) -> List[Dict[str, any]]:
        """
        Extract images using trafilatura (primary method).
        
        Args:
            url: Article URL to scrape
            
        Returns:
            List of image dictionaries with URL and score
        """
        try:
            self.logger.info(f"Trying trafilatura for {url}")
            
            # Download the webpage
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return []
            
            # Extract metadata which includes main image
            metadata = trafilatura.metadata.extract_metadata(downloaded)
            images = []
            
            if metadata and hasattr(metadata, 'image') and metadata.image:
                main_img_url = urljoin(url, metadata.image)
                score = self.score_image_relevance(main_img_url, source_method="trafilatura_main")
                images.append({
                    'url': main_img_url,
                    'score': score,
                    'source': 'trafilatura_main'
                })
                self.logger.info(f"Trafilatura found main image: {metadata.image} (score: {score})")
            
            # Also try to extract content and look for images in it
            content = trafilatura.extract(downloaded, include_images=True, include_links=True)
            if content:
                # Parse content for additional images
                soup = BeautifulSoup(content, 'html.parser')
                img_tags = soup.find_all('img')
                seen_urls = {img['url'] for img in images}
                
                for img in img_tags:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        full_url = urljoin(url, src)
                        if full_url not in seen_urls:
                            score = self.score_image_relevance(full_url, img, "trafilatura")
                            images.append({
                                'url': full_url,
                                'score': score,
                                'source': 'trafilatura'
                            })
                            seen_urls.add(full_url)
            
            return images
            
        except Exception as e:
            self.logger.warning(f"Trafilatura failed for {url}: {e}")
            return []

    def extract_images_newspaper(self, url: str) -> List[Dict[str, any]]:
        """
        Extract images using newspaper3k (secondary method).
        
        Args:
            url: Article URL to scrape
            
        Returns:
            List of image dictionaries with URL and score
        """
        try:
            self.logger.info(f"Trying newspaper3k for {url}")
            
            article = Article(url)
            article.download()
            article.parse()
            
            images = []
            seen_urls = set()
            
            # Get top image (highest priority)
            if article.top_image:
                full_url = urljoin(url, article.top_image)
                score = self.score_image_relevance(full_url, source_method="newspaper_top")
                images.append({
                    'url': full_url,
                    'score': score,
                    'source': 'newspaper_top'
                })
                seen_urls.add(full_url)
                self.logger.info(f"Newspaper3k found top image: {article.top_image} (score: {score})")
            
            # Get all other images
            if article.images:
                for img_url in article.images:
                    full_url = urljoin(url, img_url)
                    if full_url not in seen_urls:
                        score = self.score_image_relevance(full_url, source_method="newspaper")
                        images.append({
                            'url': full_url,
                            'score': score,
                            'source': 'newspaper'
                        })
                        seen_urls.add(full_url)
            
            return images
            
        except Exception as e:
            self.logger.warning(f"Newspaper3k failed for {url}: {e}")
            return []

    def extract_opengraph_images(self, soup: BeautifulSoup, url: str) -> List[Dict[str, any]]:
        """
        Extract images from OpenGraph and other meta tags.
        
        Args:
            soup: BeautifulSoup object of the webpage
            url: Base URL for resolving relative URLs
            
        Returns:
            List of image dictionaries from meta tags
        """
        images = []
        
        # OpenGraph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = urljoin(url, og_image['content'])
            if not self._should_exclude_image_url(img_url):
                score = self.score_image_relevance(img_url, source_method="opengraph")
                images.append({
                    'url': img_url,
                    'score': score + 25,  # Bonus for OpenGraph
                    'source': 'opengraph'
                })
        
        # Twitter card image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            img_url = urljoin(url, twitter_image['content'])
            if not self._should_exclude_image_url(img_url):
                score = self.score_image_relevance(img_url, source_method="twitter_card")
                images.append({
                    'url': img_url,
                    'score': score + 20,  # Bonus for Twitter card
                    'source': 'twitter_card'
                })
        
        # Schema.org structured data
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Look for image in various schema types
                        schema_image = data.get('image')
                        if schema_image:
                            if isinstance(schema_image, list):
                                schema_image = schema_image[0]
                            if isinstance(schema_image, dict):
                                schema_image = schema_image.get('url', schema_image.get('@id'))
                            if isinstance(schema_image, str):
                                img_url = urljoin(url, schema_image)
                                if not self._should_exclude_image_url(img_url):
                                    score = self.score_image_relevance(img_url, source_method="schema")
                                    images.append({
                                        'url': img_url,
                                        'score': score + 22,  # Bonus for schema.org
                                        'source': 'schema'
                                    })
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        
        return images

    def extract_images_beautifulsoup(self, url: str) -> List[Dict[str, any]]:
        """
        Extract images using BeautifulSoup with filtering (fallback method).
        
        Args:
            url: Article URL to scrape
            
        Returns:
            List of image dictionaries with URL and score
        """
        try:
            self.logger.info(f"Trying BeautifulSoup for {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            images = []
            seen_urls = set()
            
            # First, try OpenGraph and meta tags (highest priority)
            meta_images = self.extract_opengraph_images(soup, url)
            images.extend(meta_images)
            seen_urls.update(img['url'] for img in meta_images)
            
            # Find all img tags
            img_tags = soup.find_all('img')
            
            for img in img_tags:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                
                if not src:
                    continue
                
                # Convert relative URLs to absolute
                full_url = urljoin(url, src)
                
                # Filter out unwanted images
                if self._should_exclude_image(img, full_url):
                    continue
                
                if full_url not in seen_urls:
                    score = self.score_image_relevance(full_url, img, "soup")
                    images.append({
                        'url': full_url,
                        'score': score,
                        'source': 'soup'
                    })
                    seen_urls.add(full_url)
            
            # Also check for picture/source elements
            picture_tags = soup.find_all('picture')
            for picture in picture_tags:
                sources = picture.find_all('source')
                for source in sources:
                    srcset = source.get('srcset')
                    if srcset:
                        # Extract first URL from srcset
                        url_part = srcset.split(',')[0].strip().split(' ')[0]
                        full_url = urljoin(url, url_part)
                        if not self._should_exclude_image_url(full_url) and full_url not in seen_urls:
                            score = self.score_image_relevance(full_url, source_method="soup")
                            images.append({
                                'url': full_url,
                                'score': score,
                                'source': 'soup'
                            })
                            seen_urls.add(full_url)
            
            return images
            
        except Exception as e:
            self.logger.warning(f"BeautifulSoup failed for {url}: {e}")
            return []

    def _should_exclude_image(self, img_tag, img_url: str) -> bool:
        """
        Determine if an image should be excluded based on various criteria.
        
        Args:
            img_tag: BeautifulSoup img tag element
            img_url: Full image URL
            
        Returns:
            True if image should be excluded
        """
        # Check URL patterns
        if self._should_exclude_image_url(img_url):
            return True
        
        # Check alt text
        alt_text = img_tag.get('alt', '').lower()
        if self.exclude_regex.search(alt_text):
            return True
        
        # Check class names
        class_names = ' '.join(img_tag.get('class', [])).lower()
        if self.exclude_regex.search(class_names):
            return True
        
        # Check dimensions if available
        width = img_tag.get('width')
        height = img_tag.get('height')
        if width and height:
            try:
                w, h = int(width), int(height)
                if w < self.min_image_size[0] or h < self.min_image_size[1]:
                    return True
            except ValueError:
                pass
        
        return False

    def _should_exclude_image_url(self, img_url: str) -> bool:
        """Check if image URL should be excluded based on patterns."""
        # Basic pattern matching
        if self.exclude_regex.search(img_url):
            return True
        
        # Additional checks for tracking pixels and non-image URLs
        parsed_url = urlparse(img_url)
        
        # Exclude tracking domains and specific tracking URLs
        tracking_domains = [
            'facebook.com', 'google-analytics.com', 'googletagmanager.com',
            'doubleclick.net', 'googlesyndication.com', 'googleadservices.com',
            'outbrain.com', 'taboola.com', 'amazon-adsystem.com'
        ]
        
        # Specific tracking URL patterns
        tracking_patterns = [
            'facebook.com/tr', 'google-analytics.com', '/pixel?', '/track?',
            '/beacon?', '/analytics?', 'googletagmanager.com'
        ]
        
        # Check for tracking domains
        if any(domain in parsed_url.netloc.lower() for domain in tracking_domains):
            return True
            
        # Check for specific tracking URL patterns
        if any(pattern in img_url.lower() for pattern in tracking_patterns):
            return True
        
        # Exclude URLs with tracking parameters
        if any(param in parsed_url.query.lower() for param in ['fbclid', 'gclid', 'utm_', 'pixel']):
            return True
        
        # Exclude very small images (likely pixels)
        if 'width=1' in img_url or 'height=1' in img_url or '1x1' in img_url:
            return True
        
        # Must have valid image extension or be from a known image CDN
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.svg'}
        path_ext = Path(parsed_url.path).suffix.lower()
        
        # Allow images from known CDNs even without extensions
        image_cdns = ['static.toiimg.com', 'images.', 'img.', 'cdn.', 'assets.']
        is_image_cdn = any(cdn in parsed_url.netloc.lower() for cdn in image_cdns)
        
        if not path_ext and not is_image_cdn:
            return True
        
        if path_ext and path_ext not in valid_extensions:
            return True
        
        return False

    def analyze_image_context(self, img_tag, article_content: str = "") -> int:
        """
        Analyze the HTML context around an image to determine relevance.
        
        Args:
            img_tag: BeautifulSoup img tag
            article_content: Article text content for comparison
            
        Returns:
            Context relevance score (0-30)
        """
        if not img_tag:
            return 0
        
        context_score = 0
        
        # Check if image is within article content areas
        parent = img_tag.parent
        for _ in range(3):  # Check up to 3 levels up
            if parent:
                parent_classes = ' '.join(parent.get('class', [])).lower()
                parent_id = parent.get('id', '').lower()
                
                # Positive indicators
                if any(indicator in parent_classes + parent_id for indicator in [
                    'article', 'content', 'story', 'body', 'post', 'main', 'entry'
                ]):
                    context_score += 15
                    break
                
                # Negative indicators
                if any(indicator in parent_classes + parent_id for indicator in [
                    'header', 'nav', 'footer', 'sidebar', 'menu', 'ad', 'widget'
                ]):
                    context_score -= 10
                    break
                
                parent = parent.parent
        
        # Check surrounding text for relevance
        try:
            # Get text around the image
            surrounding_text = ""
            if img_tag.parent:
                surrounding_text = img_tag.parent.get_text().lower()
            
            # Look for caption or figure elements
            figure_parent = img_tag.find_parent(['figure', 'div'])
            if figure_parent:
                caption = figure_parent.find(['figcaption', 'caption', 'div'])
                if caption:
                    caption_text = caption.get_text().lower()
                    if len(caption_text) > 10:  # Substantial caption
                        context_score += 10
        except:
            pass
        
        return max(0, context_score)

    def score_image_relevance(self, img_url: str, img_tag=None, source_method: str = "", article_content: str = "") -> int:
        """
        Score image relevance based on various factors.
        Higher score = more relevant.
        
        Args:
            img_url: Image URL to score
            img_tag: BeautifulSoup img tag (if available)
            source_method: Method that found this image (trafilatura, newspaper, soup)
            
        Returns:
            Relevance score (0-100)
        """
        score = 50  # Base score
        
        # Source method scoring (prioritize trafilatura and newspaper main images)
        if source_method == "trafilatura_main":
            score += 30  # Highest priority for main article image
        elif source_method == "newspaper_top":
            score += 25  # High priority for newspaper top image
        elif source_method == "trafilatura":
            score += 15
        elif source_method == "newspaper":
            score += 10
        elif source_method == "soup":
            score += 5
        
        # URL-based scoring with improved logo detection
        url_lower = img_url.lower()
        parsed_url = urlparse(img_url)
        
        # Positive indicators in URL
        if any(term in url_lower for term in ['featured', 'main', 'hero', 'cover', 'article']):
            score += 20
        if any(term in url_lower for term in ['large', 'big', 'full', 'original']):
            score += 12
        if 'wp-content/uploads' in url_lower:  # WordPress uploads (often article images)
            score += 10
        
        # Check for content-specific URLs (not logos)
        if any(term in url_lower for term in ['photo', 'image', 'pic', 'img']):
            score += 8
        
        # Strong negative indicators for logos and branding
        logo_indicators = [
            'logo', 'brand', 'header', 'masthead', 'watermark',
            'signature', 'emblem', 'badge', 'seal', 'mark'
        ]
        if any(term in url_lower for term in logo_indicators):
            score -= 25  # Heavy penalty for logos
        
        # Company/site branding detection
        if any(term in url_lower for term in ['toi', 'timesofindia', 'company', 'corp']):
            score -= 15
        
        # Tracking pixels and analytics (should never be selected as images)
        if 'facebook.com/tr' in url_lower or '/tr?' in url_lower:
            score -= 50  # Massive penalty for Facebook tracking pixels
        if any(pattern in url_lower for pattern in ['analytics', 'tracking', 'pixel?', 'beacon?']):
            score -= 40
        
        # Standard negative indicators
        if any(term in url_lower for term in ['thumb', 'small', 'mini', 'icon']):
            score -= 15
        if any(term in url_lower for term in ['ad', 'banner', 'widget', 'sidebar']):
            score -= 20
        if any(term in url_lower for term in ['social', 'share', 'profile', 'avatar']):
            score -= 10
        
        # Size indicators in URL (logos often have standard sizes)
        if any(size in url_lower for size in ['150x', '200x', '100x', '50x']):
            score -= 12  # Common logo sizes
        if any(size in url_lower for size in ['x150', 'x200', 'x100', 'x50']):
            score -= 12
        
        # HTML tag-based scoring (if available)
        if img_tag:
            # Check alt text for relevance
            alt_text = img_tag.get('alt', '').lower()
            if alt_text:
                if any(term in alt_text for term in ['article', 'story', 'news', 'main', 'photo']):
                    score += 10
                if any(term in alt_text for term in ['logo', 'icon', 'button', 'arrow']):
                    score -= 15
            
            # Check CSS classes
            classes = ' '.join(img_tag.get('class', [])).lower()
            if 'featured' in classes or 'hero' in classes or 'main' in classes:
                score += 15
            if any(term in classes for term in ['sidebar', 'widget', 'ad', 'banner']):
                score -= 20
            
            # Check parent elements for context
            parent = img_tag.parent
            if parent:
                parent_classes = ' '.join(parent.get('class', [])).lower()
                if 'article' in parent_classes or 'content' in parent_classes:
                    score += 10
                if 'sidebar' in parent_classes or 'footer' in parent_classes:
                    score -= 15
        
        # Add context analysis score
        if img_tag:
            context_score = self.analyze_image_context(img_tag, article_content)
            score += context_score
        
        # File extension preferences (some formats are more likely to be main images)
        if img_url.lower().endswith(('.jpg', '.jpeg')):
            score += 5  # JPEG often used for photos
        elif img_url.lower().endswith('.png'):
            score += 2  # PNG could be graphics or photos
        elif img_url.lower().endswith('.gif'):
            score -= 5  # GIFs often animations or small graphics
        
        return max(0, min(100, score))  # Clamp between 0-100

    def validate_image_size(self, img_url: str) -> bool:
        """
        Validate image size using HEAD request and optionally PIL.
        
        Args:
            img_url: Image URL to validate
            
        Returns:
            True if image meets size requirements
        """
        try:
            # Check file size with HEAD request
            head_response = self.session.head(img_url, timeout=10)
            content_length = head_response.headers.get('content-length')
            
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > self.max_file_size_mb:
                    self.logger.info(f"Image too large ({size_mb:.1f}MB): {img_url}")
                    return False
            
            # Download a small portion to check actual dimensions
            response = self.session.get(img_url, timeout=15, stream=True)
            response.raise_for_status()
            
            # Read enough bytes to determine image dimensions
            chunk_size = 1024
            data = b''
            for chunk in response.iter_content(chunk_size=chunk_size):
                data += chunk
                if len(data) > chunk_size * 10:  # Stop after 10KB
                    break
            
            try:
                img = Image.open(io.BytesIO(data))
                width, height = img.size
                
                if width < self.min_image_size[0] or height < self.min_image_size[1]:
                    self.logger.info(f"Image too small ({width}x{height}): {img_url}")
                    return False
                
                return True
                
            except Exception:
                # If we can't determine size, assume it's valid
                return True
            
        except Exception as e:
            self.logger.warning(f"Could not validate image size for {img_url}: {e}")
            return True  # Assume valid if we can't check

    def download_image(self, img_url: str, output_path: Path) -> bool:
        """
        Download an image from URL and convert it to JPG format.
        
        Args:
            img_url: Image URL to download
            output_path: Local path to save the image (will be saved as .jpg)
            
        Returns:
            True if download and conversion was successful
        """
        try:
            response = self.session.get(img_url, timeout=30)
            response.raise_for_status()
            
            # Always save as JPG
            output_path = output_path.with_suffix('.jpg')
            
            # Load image data into PIL
            image_data = io.BytesIO(response.content)
            
            # Open and process the image
            with Image.open(image_data) as img:
                # Convert to RGB if necessary (for PNG with transparency, WEBP, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as high-quality JPG
                img.save(output_path, 'JPEG', quality=90, optimize=True)
            
            self.logger.info(f"Downloaded and converted to JPG: {output_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download/convert {img_url}: {e}")
            return False

    def scrape_article_images(self, url: str) -> Optional[Dict[str, any]]:
        """
        Scrape the single most relevant image from an article URL.
        
        Args:
            url: Article URL to scrape
            
        Returns:
            Dictionary with the best image data, or None if no suitable image found
        """
        all_images = []
        
        # Method 1: Trafilatura (prioritize main images)
        images = self.extract_images_trafilatura(url)
        all_images.extend(images)
        
        # Method 2: Newspaper3k (if no high-quality image found yet)
        best_score = max([img['score'] for img in all_images], default=0)
        if best_score < 80:  # Raised threshold for better quality
            images = self.extract_images_newspaper(url)
            all_images.extend(images)
        
        # Method 3: BeautifulSoup with meta tags (only if still no good image)
        best_score = max([img['score'] for img in all_images], default=0)
        if best_score < 70:  # Raised threshold
            images = self.extract_images_beautifulsoup(url)
            all_images.extend(images)
        
        if not all_images:
            self.logger.warning(f"No images found for {url}")
            return None
        
        # Remove duplicates while preserving highest score
        seen_urls = {}
        for img in all_images:
            img_url = img['url']
            if img_url not in seen_urls or img['score'] > seen_urls[img_url]['score']:
                seen_urls[img_url] = img
        
        unique_images = list(seen_urls.values())
        
        # Sort by relevance score (highest first) and get the best one
        unique_images.sort(key=lambda x: x['score'], reverse=True)
        
        # Find the first image that passes size validation and minimum score
        MIN_ACCEPTABLE_SCORE = 40  # Minimum score to accept an image
        
        for img_data in unique_images:
            if img_data['score'] >= MIN_ACCEPTABLE_SCORE and self.validate_image_size(img_data['url']):
                self.logger.info(f"Selected best image: {img_data['url']} (score: {img_data['score']}, source: {img_data['source']})")
                return img_data
        
        # If no image meets minimum score, log the best available score
        if unique_images:
            best_score = unique_images[0]['score']
            self.logger.warning(f"No images above minimum score ({MIN_ACCEPTABLE_SCORE}) for {url}. Best score: {best_score}")
        else:
            self.logger.warning(f"No valid images found after size validation for {url}")
        
        return None

    def process_article(self, json_file_path: Path) -> bool:
        """
        Process a single JSON article file.
        
        Args:
            json_file_path: Path to the JSON file containing article metadata
            
        Returns:
            True if processing was successful
        """
        try:
            # Load JSON data
            with open(json_file_path, 'r', encoding='utf-8') as f:
                article_data = json.load(f)
            
            # Extract required fields
            title = article_data.get('title', 'Untitled')
            url = article_data.get('url')
            
            if not url:
                self.logger.error(f"No URL found in {json_file_path}")
                return False
            
            self.logger.info(f"Processing: {title}")
            
            # Create article folder
            folder_name = self.sanitize_filename(title)
            article_folder = self.output_folder / folder_name
            article_folder.mkdir(exist_ok=True)
            
            # Scrape the best image
            best_image_data = self.scrape_article_images(url)
            
            if not best_image_data:
                self.logger.warning(f"No suitable image found for: {title}")
                # Still create the JSON file even without image
                article_data['image'] = None
                article_data['processing_timestamp'] = time.time()
                
                output_json_path = article_folder / 'article_data.json'
                with open(output_json_path, 'w', encoding='utf-8') as f:
                    json.dump(article_data, f, indent=2, ensure_ascii=False)
                
                return True
            
            # Download the single best image as JPG
            img_filename = "image"  # Will become image.jpg
            img_path = article_folder / img_filename
            
            image_info = None
            if self.download_image(best_image_data['url'], img_path):
                image_info = {
                    'url': best_image_data['url'],
                    'filename': 'image.jpg',  # Always JPG now
                    'local_path': str((article_folder / 'image.jpg').relative_to(self.output_folder)),
                    'relevance_score': best_image_data['score'],
                    'source_method': best_image_data['source']
                }
                self.logger.info(f"Downloaded best image for: {title} (score: {best_image_data['score']})")
            else:
                self.logger.error(f"Failed to download image for: {title}")
                image_info = None
            
            # Update article data with image information
            article_data['image'] = image_info
            article_data['processing_timestamp'] = time.time()
            
            # Save updated JSON
            output_json_path = article_folder / 'article_data.json'
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, indent=2, ensure_ascii=False)
            
            success_msg = f"Completed: {title}"
            if image_info:
                success_msg += f" (1 image, score: {best_image_data['score']})"
            else:
                success_msg += " (no image)"
            self.logger.info(success_msg)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process {json_file_path}: {e}")
            return False

    def run_pipeline(self) -> Dict[str, int]:
        """
        Run the complete pipeline on all JSON files in the input folder.
        
        Returns:
            Dictionary with processing statistics
        """
        # Find all JSON files
        json_files = list(self.input_folder.glob('*.json'))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {self.input_folder}")
            return {'total': 0, 'successful': 0, 'failed': 0}
        
        self.logger.info(f"Found {len(json_files)} JSON files to process")
        
        # Process each file
        successful = 0
        failed = 0
        
        for json_file in json_files:
            try:
                if self.process_article(json_file):
                    successful += 1
                else:
                    failed += 1
            except KeyboardInterrupt:
                self.logger.info("Pipeline interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error processing {json_file}: {e}")
                failed += 1
        
        # Final statistics
        stats = {
            'total': len(json_files),
            'successful': successful,
            'failed': failed
        }
        
        self.logger.info(f"Pipeline completed: {successful}/{len(json_files)} articles processed successfully")
        return stats


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape images from article JSON files')
    parser.add_argument('--input', '-i', default='.', 
                       help='Input folder containing JSON files (default: current directory)')
    parser.add_argument('--output', '-o', default='articles+images',
                       help='Output folder for organized articles and images (default: articles+images)')
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = ImageScraperPipeline(args.input, args.output)
    stats = pipeline.run_pipeline()
    
    print(f"\n=== Pipeline Results ===")
    print(f"Total articles: {stats['total']}")
    print(f"Successfully processed: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Output folder: {pipeline.output_folder}")


if __name__ == "__main__":
    main()
