import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import openai
from functools import wraps
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
class Config:
    GEMMA_API_KEY = os.getenv('GEMMA_API_KEY', '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')
    X_BEARER_TOKEN = os.getenv('X_BEARER_TOKEN', 'AAAAAAAAAAAAAAAAAAAAALJ52wEAAAAAXwGLjK27whL9%2FIG%2BQ2Za5rxt6Yo%3DaBILLpOhotTZ6xWzROoa39qvxqDAKraBjFnWsr1YwnXrP9mU13')
    X_API_KEY = os.getenv('X_API_KEY', 'rDWsNJpoJpDkobmm0Eg4L1x9I')
    X_API_SECRET = os.getenv('X_API_SECRET', 'eNIsUHzoSgIioovqTLfF33NrTdByKmNBmMLAXNDRcw83Dwqp7l')
    X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN', '1809987965374095361-Dfgy5YApw1PO5wS1MIk92seVXim5y7')
    X_ACCESS_SECRET = os.getenv('X_ACCESS_SECRET', 'sWdIYhxjoFNkAjiElELwkANjD4I4DlEd3GNdR9Co1WJj9')
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    RATE_LIMIT_DELAY = 1

# Rate limiting decorator
def rate_limit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        time.sleep(Config.RATE_LIMIT_DELAY)
        return func(*args, **kwargs)
    return wrapper

class XProfileCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {Config.X_BEARER_TOKEN}',
            'Accept': 'application/json',
            'User-Agent': 'CryptoVibe/1.0'
        })

    @rate_limit
    def get_user_profile(self, username: str) -> Dict[str, Any]:
        """Get user profile information from X API"""
        try:
            # Remove @ symbol if present
            username = username.replace('@', '')
            
            # Get user info
            user_url = f"https://api.x.com/2/users/by/username/{username}"
            params = {
                'user.fields': 'description,public_metrics,created_at,verified',
                'expansions': 'pinned_tweet_id'
            }
            
            response = self.session.get(user_url, params=params, timeout=Config.REQUEST_TIMEOUT)
            
            if response.status_code == 401:
                logger.warning(f"X API authentication failed for user {username}")
                return self._create_fallback_profile(username)
            
            if response.status_code == 404:
                raise ValueError(f"User @{username} not found")
            
            if response.status_code == 429:
                logger.warning("X API rate limit exceeded, using fallback")
                return self._create_fallback_profile(username)
            
            response.raise_for_status()
            user_data = response.json()
            
            if 'data' not in user_data:
                return self._create_fallback_profile(username)
            
            user_info = user_data['data']
            
            # Get recent tweets
            tweets = self._get_user_tweets(user_info['id'])
            
            return {
                'username': username,
                'id': user_info['id'],
                'bio': user_info.get('description', ''),
                'followers': user_info.get('public_metrics', {}).get('followers_count', 0),
                'following': user_info.get('public_metrics', {}).get('following_count', 0),
                'tweets': tweets,
                'verified': user_info.get('verified', False),
                'created_at': user_info.get('created_at', ''),
                'success': True
            }
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching profile for {username}: {e}")
            return self._create_fallback_profile(username)
        except Exception as e:
            logger.error(f"Error fetching profile for {username}: {e}")
            return self._create_fallback_profile(username)

    def _get_user_tweets(self, user_id: str) -> List[str]:
        """Get recent tweets from user"""
        try:
            tweets_url = f"https://api.x.com/2/users/{user_id}/tweets"
            params = {
                'max_results': 10,
                'tweet.fields': 'text,created_at,public_metrics',
                'exclude': 'retweets,replies'
            }
            
            response = self.session.get(tweets_url, params=params, timeout=Config.REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                return []
            
            tweets_data = response.json()
            if 'data' not in tweets_data:
                return []
            
            return [tweet['text'] for tweet in tweets_data['data']]
            
        except Exception as e:
            logger.error(f"Error fetching tweets for user {user_id}: {e}")
            return []

    def _create_fallback_profile(self, username: str) -> Dict[str, Any]:
        """Create a fallback profile when API fails"""
        return {
            'username': username,
            'id': f'fallback_{username}',
            'bio': 'Profile information not available',
            'followers': 0,
            'following': 0,
            'tweets': [],
            'verified': False,
            'created_at': '',
            'success': False,
            'fallback': True
        }

class PostGenerator:
    def __init__(self):
        self.gemma_api_key = Config.GEMMA_API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.gemma_api_key}',
            'Content-Type': 'application/json'
        })

    def generate_random_posts(self, content: str, hashtags: bool, length: str) -> List[str]:
        """Generate random posts based on content idea"""
        try:
            prompt = self._create_random_prompt(content, hashtags, length)
            return self._generate_with_gemma(prompt, length)
                
        except Exception as e:
            logger.error(f"Error generating random posts: {e}")
            return self._generate_fallback_posts(content, hashtags, length)

    def generate_profile_posts(self, profile: Dict[str, Any], industry: str, 
                             tone: str, content_types: List[str], hashtags: bool) -> Dict[str, List[str]]:
        """Generate posts based on profile analysis"""
        try:
            analysis = self._analyze_profile(profile, industry)
            
            long_posts = self._generate_posts_for_profile(
                profile, analysis, industry, tone, content_types, hashtags, 'long'
            )
            
            short_posts = self._generate_posts_for_profile(
                profile, analysis, industry, tone, content_types, hashtags, 'short'
            )
            
            return {
                'long': long_posts,
                'short': short_posts,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating profile posts: {e}")
            return self._generate_fallback_profile_posts(profile, industry, tone, hashtags)

    def _analyze_profile(self, profile: Dict[str, Any], industry: str) -> str:
        """Analyze profile and return insights"""
        if profile.get('fallback'):
            return f"Profile analysis using fallback mode for @{profile['username']} in {industry} industry."
        
        bio = profile.get('bio', '')
        tweets = profile.get('tweets', [])
        followers = profile.get('followers', 0)
        
        analysis_parts = []
        
        if bio:
            analysis_parts.append(f"Bio focuses on: {bio[:100]}...")
        
        if tweets:
            analysis_parts.append(f"Recent activity shows engagement with {industry} content")
        
        if followers > 1000:
            analysis_parts.append(f"Established presence with {followers:,} followers")
        else:
            analysis_parts.append("Growing presence in the crypto space")
        
        return ". ".join(analysis_parts) if analysis_parts else "Profile analysis completed"

    def _create_random_prompt(self, content: str, hashtags: bool, length: str) -> str:
        """Create prompt for random post generation"""
        hashtag_instruction = "Include relevant hashtags" if hashtags else "Do not include hashtags"
        length_instruction = "Make posts 200+ characters" if length == 'long' else "Keep posts under 200 characters"
        
        return f"""
        Create 3 engaging crypto social media posts about: {content}
        
        Requirements:
        - {length_instruction}
        - {hashtag_instruction}
        - Make them engaging and informative
        - Use crypto terminology appropriately
        - Each post should be unique and creative
        
        Return only the posts, one per line.
        """

    def _generate_with_gemma(self, prompt: str, length: str) -> List[str]:
        """Generate posts using Gemma API"""
        try:
            # Gemma API endpoint (using OpenRouter format)
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            payload = {
                "model": "google/gemma-2-9b-it:free",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 800,
                "temperature": 0.7
            }
            
            response = self.session.post(url, json=payload, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            generated_text = data['choices'][0]['message']['content'].strip()
            
            # Parse the generated text into posts
            posts = [post.strip() for post in generated_text.split('\n') if post.strip() and not post.strip().startswith('#')]
            
            # Filter out numbering and clean up posts
            cleaned_posts = []
            for post in posts:
                # Remove number prefixes like "1.", "2.", etc.
                cleaned_post = post.strip()
                if cleaned_post and len(cleaned_post) > 20:  # Minimum post length
                    # Remove leading numbers and dots
                    import re
                    cleaned_post = re.sub(r'^\d+\.?\s*', '', cleaned_post)
                    cleaned_posts.append(cleaned_post)
            
            return cleaned_posts[:3] if len(cleaned_posts) >= 3 else cleaned_posts or self._generate_fallback_posts("crypto content", True, length)
            
        except Exception as e:
            logger.error(f"Gemma API error: {e}")
            raise

    def _generate_with_fallback(self, content: str, hashtags: bool, length: str) -> List[str]:
        """Generate posts using fallback method"""
        templates = self._get_post_templates(length)
        posts = []
        
        for i, template in enumerate(templates[:3]):
            post = template.format(content=content, number=i+1)
            
            if hashtags:
                crypto_hashtags = ["#crypto", "#blockchain", "#DeFi", "#Bitcoin", "#Ethereum"]
                selected_hashtags = crypto_hashtags[:2]
                post += f" {' '.join(selected_hashtags)}"
            
            posts.append(post)
        
        return posts

    def _get_post_templates(self, length: str) -> List[str]:
        """Get post templates based on length"""
        if length == 'long':
            return [
                "🚀 Exciting developments in {content}! The crypto market continues to evolve with innovative solutions that are reshaping the financial landscape. What are your thoughts on these recent changes?",
                "📈 Market analysis: {content} is showing remarkable potential in the current cycle. With institutional adoption growing and technology advancing, we're seeing unprecedented opportunities for growth.",
                "💎 Deep dive into {content}: The fundamentals are strong, community engagement is high, and the technology behind it is revolutionary. This could be a game-changer for the entire ecosystem."
            ]
        else:
            return [
                "🔥 {content} is trending! What's your take?",
                "📊 Latest on {content} - bullish or bearish?",
                "💡 Quick thought: {content} could be huge!"
            ]

    def _generate_posts_for_profile(self, profile: Dict[str, Any], analysis: str, 
                                  industry: str, tone: str, content_types: List[str], 
                                  hashtags: bool, length: str) -> List[str]:
        """Generate posts for specific profile"""
        try:
            prompt = self._create_profile_prompt(profile, analysis, industry, tone, content_types, hashtags, length)
            return self._generate_with_gemma(prompt, length)
                
        except Exception as e:
            logger.error(f"Error generating profile posts: {e}")
            return self._generate_profile_fallback(profile, industry, tone, content_types, hashtags, length)

    def _create_profile_prompt(self, profile: Dict[str, Any], analysis: str, 
                             industry: str, tone: str, content_types: List[str], 
                             hashtags: bool, length: str) -> str:
        """Create prompt for profile-based post generation"""
        username = profile.get('username', 'user')
        bio = profile.get('bio', '')
        
        hashtag_instruction = "Include relevant hashtags" if hashtags else "Do not include hashtags"
        length_instruction = "Make posts 200+ characters" if length == 'long' else "Keep posts under 200 characters"
        tone_instruction = f"Use a {tone} tone"
        content_instruction = f"Focus on {', '.join(content_types)} content"
        
        return f"""
        Create 3 social media posts that would match the style of @{username} in the {industry} industry.
        
        Profile Context:
        - Bio: {bio}
        - Analysis: {analysis}
        
        Requirements:
        - {length_instruction}
        - {hashtag_instruction}
        - {tone_instruction}
        - {content_instruction}
        - Match the user's apparent style and interests
        - Make posts authentic and engaging
        
        Return only the posts, one per line.
        """

    def _generate_profile_fallback(self, profile: Dict[str, Any], industry: str, 
                                 tone: str, content_types: List[str], hashtags: bool, length: str) -> List[str]:
        """Generate profile posts using fallback method"""
        username = profile.get('username', 'user')
        templates = self._get_profile_templates(industry, tone, length)
        posts = []
        
        for template in templates[:3]:
            post = template.format(username=username, industry=industry)
            
            if hashtags:
                industry_hashtags = {
                    'defi': ['#DeFi', '#YieldFarming'],
                    'crypto': ['#Crypto', '#Blockchain'],
                    'nft': ['#NFT', '#DigitalArt'],
                    'airdrop': ['#Airdrop', '#FreeCrypto'],
                    'blockchain': ['#Blockchain', '#Web3']
                }
                tags = industry_hashtags.get(industry, ['#Crypto', '#Blockchain'])
                post += f" {' '.join(tags)}"
            
            posts.append(post)
        
        return posts

    def _get_profile_templates(self, industry: str, tone: str, length: str) -> List[str]:
        """Get profile-specific templates"""
        if length == 'long':
            return [
                f"Diving deep into {industry} today! The landscape is rapidly evolving with new protocols and innovations emerging weekly. What excites me most is the potential for mass adoption.",
                f"Been analyzing the {industry} market trends and I'm seeing some interesting patterns. The technology is maturing and institutional interest is growing significantly.",
                f"Community discussion: What's your take on the current state of {industry}? I believe we're still in the early stages of a massive transformation."
            ]
        else:
            return [
                f"Bullish on {industry} developments! 🚀",
                f"Latest {industry} news got me excited!",
                f"Who else is watching {industry} closely?"
            ]

    def _generate_fallback_posts(self, content: str, hashtags: bool, length: str) -> List[str]:
        """Generate fallback posts when all else fails"""
        base_posts = [
            f"Interesting developments in {content}! 🚀",
            f"Market thoughts: {content} is worth watching 📈",
            f"What's everyone's take on {content}? 💭"
        ]
        
        if hashtags:
            base_posts = [post + " #crypto #blockchain" for post in base_posts]
        
        return base_posts

    def _generate_fallback_profile_posts(self, profile: Dict[str, Any], industry: str, 
                                       tone: str, hashtags: bool) -> Dict[str, List[str]]:
        """Generate fallback profile posts"""
        username = profile.get('username', 'user')
        
        long_posts = [
            f"Exploring {industry} opportunities today! There's so much innovation happening in this space.",
            f"The {industry} ecosystem continues to evolve with new protocols and features being released regularly.",
            f"Community insight: The future of {industry} looks incredibly promising with growing adoption."
        ]
        
        short_posts = [
            f"Bullish on {industry}! 🚀",
            f"{industry} developments looking good 📈",
            f"Excited about {industry} growth! 💎"
        ]
        
        if hashtags:
            long_posts = [post + " #crypto #blockchain" for post in long_posts]
            short_posts = [post + " #crypto #blockchain" for post in short_posts]
        
        return {
            'long': long_posts,
            'short': short_posts
        }

# Initialize services
crawler = XProfileCrawler()
generator = PostGenerator()

@app.route('/')
def index():
    """Serve the main index page"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({'error': 'Index page not found'}), 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    try:
        return send_from_directory('.', filename)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/generate-posts', methods=['POST'])
def generate_posts():
    """Main endpoint for post generation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        post_type = data.get('type')
        
        if post_type == 'random':
            return handle_random_posts(data)
        elif post_type == 'profile':
            return handle_profile_posts(data)
        else:
            return jsonify({'success': False, 'error': 'Invalid post type'}), 400
            
    except Exception as e:
        logger.error(f"Error in generate_posts: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

def handle_random_posts(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle random post generation"""
    try:
        content = data.get('content', '').strip()
        hashtags = data.get('hashtags', False)
        length = data.get('length', 'short')
        
        if not content:
            return jsonify({'success': False, 'error': 'Content is required'}), 400
        
        posts = generator.generate_random_posts(content, hashtags, length)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'type': 'random'
        })
        
    except Exception as e:
        logger.error(f"Error handling random posts: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate random posts'}), 500

def handle_profile_posts(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle profile-based post generation"""
    try:
        username = data.get('username', '').strip()
        industry = data.get('industry', '')
        tone = data.get('tone', '')
        content_types = data.get('contentTypes', [])
        hashtags = data.get('hashtags', False)
        
        if not username:
            return jsonify({'success': False, 'error': 'Username is required'}), 400
        
        if not industry:
            return jsonify({'success': False, 'error': 'Industry is required'}), 400
        
        if not tone:
            return jsonify({'success': False, 'error': 'Tone is required'}), 400
        
        if not content_types:
            return jsonify({'success': False, 'error': 'Content types are required'}), 400
        
        # Get profile data
        profile = crawler.get_user_profile(username)
        
        # Generate posts
        posts = generator.generate_profile_posts(profile, industry, tone, content_types, hashtags)
        
        return jsonify({
            'success': True,
            'profile': {
                'username': profile['username'],
                'bio': profile['bio'],
                'followers': profile['followers'],
                'analysis': posts.get('analysis', 'Profile analysis completed')
            },
            'posts': {
                'long': posts['long'],
                'short': posts['short']
            },
            'type': 'profile'
        })
        
    except Exception as e:
        logger.error(f"Error handling profile posts: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate profile posts'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting CryptoVibe server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
