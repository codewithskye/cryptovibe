document.addEventListener('DOMContentLoaded', () => {
    console.log('[CryptoVibe] JS Loaded');

    // DOM Elements
    const pageLoader = document.getElementById('loader');
    const container = document.getElementById('container');
    const greeting = document.getElementById('greeting');
    const greetingText = document.getElementById('greetingText');
    const modeSelection = document.getElementById('modeSelection');
    const randomPostForm = document.getElementById('randomPostForm');
    const profileForm = document.getElementById('profileForm');
    const generateRandomBtn = document.getElementById('generateRandomBtn');
    const generateProfileBtn = document.getElementById('generateProfileBtn');
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loadingText');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    const errorText = document.getElementById('errorText');
    const profileSummary = document.getElementById('profileSummary');
    const randomResults = document.getElementById('randomResults');
    const profileResults = document.getElementById('profileResults');
    const xInput = document.getElementById('xInput');
    const postContent = document.getElementById('postContent');
    const industry = document.getElementById('industry');
    const toneStyle = document.getElementById('toneStyle');
    const tradingViewWidget = document.getElementById('tradingview_widget');
    const menuToggle = document.getElementById('menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    const contentCharCount = document.getElementById('contentCharCount');

    // Configuration
    const CONFIG = {
        API_BASE_URL: window.location.origin,
        MAX_RETRIES: 3,
        RETRY_DELAY: 1000,
        DEBOUNCE_DELAY: 300,
        MAX_POST_LENGTH: 500
    };

    // Random Crypto Vibe Words
    const cryptoVibes = [
        'HODLers', 'Moonshooters', 'Blockchain Bosses', 'DeFi Degens', 'Crypto Crusaders',
        'Token Titans', 'Web3 Warriors', 'Airdrop Avengers', 'NFT Ninjas', 'Chain Chasers',
        'Satoshi Soldiers', 'Whale Whisperers', 'Altcoin Alphas', 'Pump Pirates', 'Diamond Hands',
        'Yield Farmers', 'Liquidity Legends', 'Bag Holders', 'Hashrate Heroes', 'Bullrun Believers',
        'Ledger Legends', 'Smart Contract Sorcerers', 'Shill Squad', 'Rugpull Resisters', 'FOMO Fanatics',
        'Gas Fee Gladiators', 'Stablecoin Sentinels', 'Metaverse Mavericks', 'Protocol Pioneers', 'Genesis Gang'
    ];

    // Debounce utility
    function debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // Initialize Page
    function initializePage() {
        if (!pageLoader || !container) {
            console.warn('[CryptoVibe] Essential elements not found');
            return;
        }

        // Set initial states
        pageLoader.style.display = 'flex';
        container.style.display = 'none';
        container.classList.add('hidden');

        // Set greeting
        if (greetingText) {
            const hour = new Date().getHours();
            const vibe = cryptoVibes[Math.floor(Math.random() * cryptoVibes.length)];
            const greetingMessage = hour < 12 ? `Good Morning, ${vibe}!` :
                                  hour < 17 ? `Good Afternoon, ${vibe}!` :
                                  `Good Evening, ${vibe}!`;
            greetingText.textContent = greetingMessage;
        }

        // Hide loading and results initially
        hideElement(loading);
        hideElement(results);
        hideElement(error);

        // Start loading animation
        const progress = pageLoader.querySelector('.progress');
        if (progress) {
            progress.style.animation = 'progress 1.5s ease-in-out forwards';
        }

        // Transition to main content
        setTimeout(() => {
            hideElement(pageLoader);
            showElement(container);
            if (greeting) showElement(greeting);
            if (modeSelection) showElement(modeSelection);
        }, 1500);
    }

    // Initialize TradingView Widget
    function initializeTradingView() {
        if (tradingViewWidget && typeof TradingView !== 'undefined') {
            try {
                new TradingView.widget({
                    "width": "100%",
                    "height": "600",
                    "symbol": "BITSTAMP:BTCUSD",
                    "interval": "D",
                    "timezone": "Etc/UTC",
                    "theme": "light",
                    "style": "1",
                    "locale": "en",
                    "toolbar_bg": "#f1f3f6",
                    "enable_publishing": false,
                    "allow_symbol_change": true,
                    "container_id": "tradingview_widget"
                });
            } catch (e) {
                console.error('[CryptoVibe] TradingView widget failed to load:', e);
            }
        }
    }

    // Utility Functions
    function showElement(element) {
        if (element) {
            element.style.display = 'block';
            element.classList.remove('hidden');
        }
    }

    function hideElement(element) {
        if (element) {
            element.style.display = 'none';
            element.classList.add('hidden');
        }
    }

    function showError(message) {
        if (error && errorText) {
            errorText.textContent = message;
            showElement(error);
            setTimeout(() => hideElement(error), 8000);
        }
    }

    function showLoading(message = 'Processing...') {
        if (loading && loadingText) {
            loadingText.textContent = message;
            showElement(loading);
            hideElement(results);
            hideElement(error);
        }
    }

    function hideLoading() {
        hideElement(loading);
    }

    // Form Validation
    function validateRandomForm() {
        const content = postContent?.value?.trim();
        const hashtagChoice = getHashtagChoice('random');
        const lengthChoice = getPostLength();

        if (!content) {
            showError('Please enter a post content idea.');
            postContent?.focus();
            return false;
        }

        if (content.length > CONFIG.MAX_POST_LENGTH) {
            showError(`Post idea is too long. Maximum ${CONFIG.MAX_POST_LENGTH} characters allowed.`);
            postContent?.focus();
            return false;
        }

        if (!hashtagChoice) {
            showError('Please select whether to include hashtags.');
            return false;
        }

        if (!lengthChoice) {
            showError('Please select a post length.');
            return false;
        }

        return true;
    }

    function validateProfileForm() {
        const username = xInput?.value?.trim();
        const selectedIndustry = industry?.value;
        const tone = toneStyle?.value;
        const contentTypes = getSelectedContentTypes();
        const hashtagChoice = getHashtagChoice('profile');

        if (!username) {
            showError('Please enter an X username or profile URL.');
            xInput?.focus();
            return false;
        }

        if (!selectedIndustry) {
            showError('Please select an industry.');
            industry?.focus();
            return false;
        }

        if (!tone) {
            showError('Please select a tone style.');
            toneStyle?.focus();
            return false;
        }

        if (contentTypes.length === 0) {
            showError('Please select at least one content type.');
            return false;
        }

        if (!hashtagChoice) {
            showError('Please select whether to include hashtags.');
            return false;
        }

        return true;
    }

    // Helper Functions
    function extractUsername(input) {
        if (!input) return '';
        input = input.trim().replace('@', '');
        const urlMatch = input.match(/(?:x\.com|twitter\.com)\/([a-zA-Z0-9_]+)/);
        return urlMatch ? urlMatch[1] : input.replace(/[^a-zA-Z0-9_]/g, '');
    }

    function getSelectedContentTypes() {
        const types = [];
        ['announcement', 'education', 'market', 'community'].forEach(type => {
            const checkbox = document.getElementById(type);
            if (checkbox?.checked) types.push(type);
        });
        return types;
    }

    function getHashtagChoice(formType) {
        const yesId = formType === 'random' ? 'randomHashtagsYes' : 'hashtagsYes';
        const noId = formType === 'random' ? 'randomHashtagsNo' : 'hashtagsNo';
        const yesRadio = document.getElementById(yesId);
        const noRadio = document.getElementById(noId);
        return yesRadio?.checked ? 'yes' : noRadio?.checked ? 'no' : '';
    }

    function getPostLength() {
        const longRadio = document.getElementById('longPost');
        const shortRadio = document.getElementById('shortPost');
        return longRadio?.checked ? 'long' : shortRadio?.checked ? 'short' : '';
    }

    // API Functions
    async function makeAPICall(endpoint, data, retries = CONFIG.MAX_RETRIES) {
        for (let attempt = 0; attempt < retries; attempt++) {
            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (!response.ok) {
                    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
                }

                const result = await response.json();
                return result;
            } catch (error) {
                console.error(`[CryptoVibe] API call attempt ${attempt + 1} failed:`, error);
                
                if (attempt === retries - 1) {
                    throw error;
                }
                
                await new Promise(resolve => setTimeout(resolve, CONFIG.RETRY_DELAY * (attempt + 1)));
            }
        }
    }

    async function generateRandomPosts() {
        if (!validateRandomForm()) return;

        const data = {
            type: 'random',
            content: postContent.value.trim(),
            hashtags: getHashtagChoice('random') === 'yes',
            length: getPostLength()
        };

        try {
            showLoading('Generating random posts...');
            const response = await makeAPICall('/generate-posts', data);
            
            if (response.success) {
                displayRandomResults(response.posts);
            } else {
                showError(response.error || 'Failed to generate posts');
            }
        } catch (error) {
            console.error('[CryptoVibe] Random post generation failed:', error);
            showError('Failed to generate posts. Please try again.');
        } finally {
            hideLoading();
        }
    }

    async function generateProfilePosts() {
        if (!validateProfileForm()) return;

        const data = {
            type: 'profile',
            username: extractUsername(xInput.value),
            industry: industry.value,
            tone: toneStyle.value,
            contentTypes: getSelectedContentTypes(),
            hashtags: getHashtagChoice('profile') === 'yes'
        };

        try {
            showLoading('Analyzing profile and generating posts...');
            const response = await makeAPICall('/generate-posts', data);
            
            if (response.success) {
                displayProfileResults(response.profile, response.posts);
            } else {
                showError(response.error || 'Failed to generate profile posts');
            }
        } catch (error) {
            console.error('[CryptoVibe] Profile post generation failed:', error);
            showError('Failed to generate profile posts. Please try again.');
        } finally {
            hideLoading();
        }
    }

    // Display Results
    function displayRandomResults(posts) {
        if (!randomResults) return;

        const randomPosts = document.getElementById('randomPosts');
        if (randomPosts) {
            randomPosts.innerHTML = posts.map(post => createPostElement(post)).join('');
        }

        showElement(randomResults);
        showElement(results);
        hideElement(profileResults);
        hideElement(profileSummary);
    }

    function displayProfileResults(profile, posts) {
        if (!profileResults) return;

        // Display profile summary
        if (profileSummary && profile) {
            const profileInfo = document.getElementById('profileInfo');
            if (profileInfo) {
                profileInfo.innerHTML = `
                    <div class="profile-card">
                        <h4>@${profile.username}</h4>
                        <p><strong>Followers:</strong> ${profile.followers?.toLocaleString() || 'N/A'}</p>
                        <p><strong>Bio:</strong> ${profile.bio || 'No bio available'}</p>
                        <p><strong>Analysis:</strong> ${profile.analysis || 'Profile analysis completed'}</p>
                    </div>
                `;
            }
            showElement(profileSummary);
        }

        // Display posts
        const longPosts = document.getElementById('longPosts');
        const shortPosts = document.getElementById('shortPosts');
        
        if (longPosts && posts.long) {
            longPosts.innerHTML = posts.long.map(post => createPostElement(post)).join('');
        }
        
        if (shortPosts && posts.short) {
            shortPosts.innerHTML = posts.short.map(post => createPostElement(post)).join('');
        }

        showElement(profileResults);
        showElement(results);
        hideElement(randomResults);
    }

    function createPostElement(post) {
        const postId = Math.random().toString(36).substr(2, 9);
        const content = post.content || post;
        return `
            <div class="post-item" data-post-id="${postId}">
                <div class="post-content">${content}</div>
                <div class="post-meta">
                    <span class="post-length">${content.length} characters</span>
                    <button class="copy-btn" onclick="copyPostToClipboard('${postId}')">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
            </div>
        `;
    }

    // Copy to clipboard function
    window.copyPostToClipboard = function(postId) {
        const postElement = document.querySelector(`[data-post-id="${postId}"]`);
        if (postElement) {
            const content = postElement.querySelector('.post-content').textContent;
            navigator.clipboard.writeText(content).then(() => {
                // Show success feedback
                const copyBtn = postElement.querySelector('.copy-btn');
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                copyBtn.style.backgroundColor = '#10b981';
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                    copyBtn.style.backgroundColor = '';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text:', err);
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = content;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                const copyBtn = postElement.querySelector('.copy-btn');
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                }, 2000);
            });
        }
    };

    // Event Listeners
    function setupEventListeners() {
        // Mobile menu toggle
        if (menuToggle && navLinks) {
            menuToggle.addEventListener('click', () => {
                navLinks.classList.toggle('active');
                menuToggle.classList.toggle('open');
            });
        }

        // Form navigation
        const postTypeRadios = document.querySelectorAll('input[name="postType"]');
        postTypeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                if (randomPostForm && profileForm) {
                    hideElement(randomPostForm);
                    hideElement(profileForm);
                    hideElement(results);
                    hideElement(error);
                    
                    if (radio.value === 'random') {
                        showElement(randomPostForm);
                    } else {
                        showElement(profileForm);
                    }
                }
            });
        });

        // Character counter for post content
        if (postContent && contentCharCount) {
            const updateCharCount = debounce(() => {
                const count = postContent.value.length;
                contentCharCount.textContent = count;
                contentCharCount.style.color = count > CONFIG.MAX_POST_LENGTH ? 'var(--error-color)' : '#666';
            }, CONFIG.DEBOUNCE_DELAY);

            postContent.addEventListener('input', updateCharCount);
            postContent.addEventListener('paste', () => setTimeout(updateCharCount, 10));
        }

        // Generate button event listeners
        if (generateRandomBtn) {
            generateRandomBtn.addEventListener('click', generateRandomPosts);
        }

        if (generateProfileBtn) {
            generateProfileBtn.addEventListener('click', generateProfilePosts);
        }

        // Input validation feedback
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (input.hasAttribute('required') && !input.value.trim()) {
                    input.classList.add('error');
                } else {
                    input.classList.remove('error');
                }
            });

            input.addEventListener('input', () => {
                if (input.classList.contains('error') && input.value.trim()) {
                    input.classList.remove('error');
                }
            });
        });

        // Touch events for mobile
        addTouchEvents();
    }

    // Touch Events for Mobile
    function addTouchEvents() {
        const buttons = document.querySelectorAll('button, .cta-btn');
        buttons.forEach(button => {
            button.addEventListener('touchstart', () => {
                button.classList.add('active-touch');
            });
            
            button.addEventListener('touchend', () => {
                button.classList.remove('active-touch');
            });
            
            button.addEventListener('touchcancel', () => {
                button.classList.remove('active-touch');
            });
        });

        // Prevent double-tap zoom on buttons
        buttons.forEach(button => {
            button.addEventListener('touchend', (e) => {
                e.preventDefault();
            });
        });
    }

    // Initialize everything
    initializePage();
    initializeTradingView();
    setupEventListeners();

    // Service Worker Registration (Optional)
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('[CryptoVibe] Service Worker registered');
                })
                .catch(error => {
                    console.log('[CryptoVibe] Service Worker registration failed');
                });
        });
    }
});
