class ProductSearchApp {
    constructor() {
        this.currentPage = 1;
        this.perPage = 20;
        this.currentFilters = {};
        this.currentQuery = '';
        this.facetsData = {};
        this.suggestionTimeout = null;
        this.suggestionsDropdown = document.getElementById('suggestionsDropdown');
        this.headerSuggestionsDropdown = document.getElementById('headerSuggestionsDropdown');
        
        // Check if suggestionsDropdown is found
        if (!this.suggestionsDropdown) {
            console.error('❌ suggestionsDropdown element not found!');
        }
        if (!this.headerSuggestionsDropdown) {
            console.error('❌ headerSuggestionsDropdown element not found!');
        }
        
        this.init();
    }

    init() {
        // Add global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.showError('An unexpected error occurred. Please refresh the page.');
        });

        // Add unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showError('A network error occurred. Please check your connection.');
        });

        this.setupLandingPage();
        this.setupSearchResultsPage();
        this.loadFacets();
        this.performInitialSearch();
    }

    setupLandingPage() {
        const searchInput = document.getElementById('mainSearch');
        const voiceBtn = document.getElementById('voiceBtn');
        const imageBtn = document.getElementById('imageBtn');
        const burgerMenu = document.getElementById('burgerMenu');
        const burgerDropdown = document.getElementById('burgerDropdown');
        const logo = document.getElementById('logo');

        // Logo click opens admin page
        logo.addEventListener('click', () => {
            window.open('/admin', '_blank');
        });

        // Search functionality
        searchInput.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value);
        });

        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && searchInput.value.trim()) {
                this.transitionToSearchResults(searchInput.value.trim());
            }
        });

        // Voice input functionality
        voiceBtn.addEventListener('click', () => {
            this.startVoiceInput(searchInput);
        });

        // Image input functionality
        imageBtn.addEventListener('click', () => {
            this.startImageInput(searchInput);
        });

        // Burger menu functionality
        let burgerOpen = false;
        burgerMenu.addEventListener('click', (e) => {
            e.stopPropagation();
            burgerOpen = !burgerOpen;
            burgerDropdown.style.display = burgerOpen ? 'block' : 'none';
        });

        document.addEventListener('click', (e) => {
            if (!burgerMenu.contains(e.target) && !burgerDropdown.contains(e.target)) {
                burgerDropdown.style.display = 'none';
                burgerOpen = false;
            }
        });

        // Suggestions dropdown
        searchInput.addEventListener('focus', () => {
            if (this.suggestionsDropdown && this.suggestionsDropdown.children.length > 0) {
                this.suggestionsDropdown.style.display = 'block';
            }
        });

        document.addEventListener('click', (e) => {
            if (this.suggestionsDropdown && !searchInput.contains(e.target) && !this.suggestionsDropdown.contains(e.target)) {
                this.suggestionsDropdown.style.display = 'none';
            }
            if (this.headerSuggestionsDropdown && !searchInput.contains(e.target) && !this.headerSuggestionsDropdown.contains(e.target)) {
                this.headerSuggestionsDropdown.style.display = 'none';
            }
        });
    }

    setupSearchResultsPage() {
        const headerSearch = document.getElementById('headerSearch');
        const voiceBtnHeader = document.getElementById('voiceBtnHeader');
        const imageBtnHeader = document.getElementById('imageBtnHeader');
        const headerBurgerMenu = document.getElementById('headerBurgerMenu');
        const headerBurgerDropdown = document.getElementById('headerBurgerDropdown');

        // Header search functionality
        headerSearch.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value);
        });

        headerSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.currentPage = 1;
                this.performSearch(this.currentPage);
            }
        });

        // Header voice input functionality
        voiceBtnHeader.addEventListener('click', () => {
            this.startVoiceInput(headerSearch);
        });

        // Header image input functionality
        imageBtnHeader.addEventListener('click', () => {
            this.startImageInput(headerSearch);
        });

        // Header suggestions dropdown
        headerSearch.addEventListener('focus', () => {
            if (this.headerSuggestionsDropdown && this.headerSuggestionsDropdown.children.length > 0) {
                this.headerSuggestionsDropdown.style.display = 'block';
            }
        });

        // Filter search functionality
        const brandSearch = document.getElementById('brandSearch');
        const categorySearch = document.getElementById('categorySearch');
        const clearFiltersBtn = document.getElementById('clearFilters');

        if (brandSearch) {
            brandSearch.addEventListener('input', (e) => {
                this.filterBrandOptions(e.target.value);
            });
        }

        if (categorySearch) {
            categorySearch.addEventListener('input', (e) => {
                this.filterCategoryOptions(e.target.value);
            });
        }

        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearAllFilters();
                this.updateFilters();
            });
        }

        // Category filter bar functionality
        const clearCategoryFilters = document.getElementById('clearCategoryFilters');
        if (clearCategoryFilters) {
            clearCategoryFilters.addEventListener('click', () => {
                this.clearCategoryFilters();
            });
        }

        // Header burger menu functionality
        let headerBurgerOpen = false;
        headerBurgerMenu.addEventListener('click', (e) => {
            e.stopPropagation();
            headerBurgerOpen = !headerBurgerOpen;
            headerBurgerDropdown.style.display = headerBurgerOpen ? 'block' : 'none';
        });

        document.addEventListener('click', (e) => {
            if (!headerBurgerMenu.contains(e.target) && !headerBurgerDropdown.contains(e.target)) {
                headerBurgerDropdown.style.display = 'none';
                headerBurgerOpen = false;
            }
        });

        // Filter functionality
        document.getElementById('clearFilters').addEventListener('click', () => {
            this.clearAllFilters();
        });





        // Modal close functionality
        const modalElement = document.getElementById('productModal');
        if (modalElement) {
            // Close modal when clicking the close button
            const closeButtons = modalElement.querySelectorAll('[data-bs-dismiss="modal"], .btn-close');
            closeButtons.forEach(button => {
                button.addEventListener('click', () => {
                    this.closeModal();
                });
            });

            // Close modal when clicking outside
            modalElement.addEventListener('click', (e) => {
                if (e.target === modalElement) {
                    this.closeModal();
                }
            });

            // Close modal with Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    if (modalElement.classList.contains('show')) {
                        this.closeModal();
                    }
                }
            });
        }

        document.getElementById('sortSelect').addEventListener('change', (e) => {
            this.currentFilters.sort = e.target.value;
            this.currentPage = 1;
            this.performSearch(this.currentPage);
        });

        // Price range inputs
        document.getElementById('minPrice').addEventListener('change', () => {
            this.updateFilters();
        });

        document.getElementById('maxPrice').addEventListener('change', () => {
            this.updateFilters();
        });

        // Availability filters
        document.getElementById('availableOnly').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.currentFilters.availability = true;
            } else {
                delete this.currentFilters.availability;
            }
            this.updateFilters();
        });

        document.getElementById('inStock').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.currentFilters.stock = true;
            } else {
                delete this.currentFilters.stock;
            }
            this.updateFilters();
        });

        // Setup price range slider
        this.setupPriceRangeSlider();
    }

    transitionToSearchResults(query) {
        this.currentQuery = query;
        
        // Hide landing page
        const landingContainer = document.getElementById('landingContainer');
        if (landingContainer) {
            landingContainer.style.display = 'none';
        }
        
        // Show search results page
        const mainContent = document.getElementById('mainContent');
        if (mainContent) {
            mainContent.style.display = 'block';
        } else {
            console.error('Main content element not found!');
        }
        
        // Set the header search value
        const headerSearch = document.getElementById('headerSearch');
        if (headerSearch) {
            headerSearch.value = query;
        }
        
        // Perform search
        this.currentPage = 1;
        this.performSearch(this.currentPage);
    }

    async handleSearchInput(query) {
        this.currentQuery = query;

        // Clear previous timeout
        if (this.suggestionTimeout) {
            clearTimeout(this.suggestionTimeout);
        }

        // Get suggestions with debouncing
        if (query.length >= 2) {
            this.suggestionTimeout = setTimeout(() => {
                this.getSuggestions(query);
            }, 300);
        } else {
            if (this.suggestionsDropdown) {
                this.suggestionsDropdown.style.display = 'none';
            }
            if (this.headerSuggestionsDropdown) {
                this.headerSuggestionsDropdown.style.display = 'none';
            }
        }
    }



    async getSuggestions(query) {
        if (!query || query.length < 2) {
            this.hideSuggestions();
            return;
        }

        try {
            // Get product suggestions
            const suggestionsResponse = await fetch(`/suggestions?q=${encodeURIComponent(query)}&limit=5&fuzzy=true`);
            const suggestions = await suggestionsResponse.json();

            // Get category suggestions
            const categoriesResponse = await fetch(`/categories/search?q=${encodeURIComponent(query)}&limit=3`);
            const categories = await categoriesResponse.json();

            // Get brand suggestions
            const brandsResponse = await fetch(`/brands/search?q=${encodeURIComponent(query)}&limit=3`);
            const brands = await brandsResponse.json();

            // Display all suggestions
            this.displaySuggestions(suggestions, categories, brands);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            this.hideSuggestions();
        }
    }

    displaySuggestions(suggestions, categories = [], brands = [], targetDropdown = null) {
        // Determine which dropdown to use
        let dropdown = targetDropdown;
        if (!dropdown) {
            // Auto-detect based on which search input is focused
            const mainSearch = document.getElementById('mainSearch');
            const headerSearch = document.getElementById('headerSearch');
            
            if (document.activeElement === headerSearch) {
                dropdown = this.headerSuggestionsDropdown;
            } else {
                dropdown = this.suggestionsDropdown;
            }
        }
        
        // Check if suggestions dropdown exists
        if (!dropdown) {
            console.warn('No suggestions dropdown element found');
            return;
        }

        let html = '';

        // Display regular search suggestions
        if (suggestions && suggestions.length > 0) {
            html += '<div class="suggestion-section"><div class="suggestion-title">Search Suggestions</div>';
            suggestions.forEach(suggestion => {
                html += `
                    <div class="suggestion-item" onclick="app.selectSuggestion('${suggestion.replace(/'/g, "\\'")}')">
                        <i class="fas fa-search suggestion-icon"></i>
                        <span>${suggestion}</span>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Display brand suggestions
        if (brands && brands.length > 0) {
            html += '<div class="suggestion-section"><div class="suggestion-title">Brands</div>';
            brands.forEach(brand => {
                const brandName = brand.name || brand.key || brand;
                const brandCount = brand.product_count || brand.total_products || brand.count || 0;
                html += `
                    <div class="suggestion-item brand-suggestion" onclick="app.selectBrandSuggestion('${brandName.replace(/'/g, "\\'")}')">
                        <i class="fas fa-tag suggestion-icon"></i>
                        <span>${brandName}</span>
                        <span class="brand-count">${brandCount} products</span>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Display category suggestions
        if (categories && categories.length > 0) {
            html += '<div class="suggestion-section"><div class="suggestion-title">Categories</div>';
            categories.forEach(category => {
                const categoryName = category.name || category.key || category;
                const categoryCount = category.product_count || category.total_products || category.count || 0;
                html += `
                    <div class="suggestion-item category-suggestion" onclick="app.selectCategorySuggestion('${categoryName.replace(/'/g, "\\'")}')">
                        <i class="fas fa-layer-group suggestion-icon"></i>
                        <span>${categoryName}</span>
                        <span class="category-count">${categoryCount} products</span>
                    </div>
                `;
            });
            html += '</div>';
        }

        if (html === '') {
            dropdown.style.display = 'none';
            return;
        }

        dropdown.innerHTML = html;
        dropdown.style.display = 'block';
        
        // Force the dropdown to be visible
        dropdown.style.visibility = 'visible';
        dropdown.style.opacity = '1';
    }

    selectSuggestion(suggestion) {
        const searchInput = document.getElementById('mainSearch');
        const headerSearch = document.getElementById('headerSearch');
        
        if (searchInput) searchInput.value = suggestion;
        if (headerSearch) headerSearch.value = suggestion;
        
        this.currentQuery = suggestion;
        if (this.suggestionsDropdown) {
            this.suggestionsDropdown.style.display = 'none';
        }
        if (this.headerSuggestionsDropdown) {
            this.headerSuggestionsDropdown.style.display = 'none';
        }
        
        // Check which page we're on and handle accordingly
        if (searchInput && searchInput.id === 'mainSearch') {
            // We're on the landing page, transition to search results
            this.transitionToSearchResults(suggestion);
        } else {
            // We're on the search results page, perform search
            this.currentPage = 1;
            this.performSearch(this.currentPage);
        }
    }

    selectCategorySuggestion(categoryName) {
        const searchInput = document.getElementById('mainSearch');
        const headerSearch = document.getElementById('headerSearch');
        
        // Set the category name as the search query
        if (searchInput) searchInput.value = categoryName;
        if (headerSearch) headerSearch.value = categoryName;
        
        this.currentQuery = categoryName;
        if (this.suggestionsDropdown) {
            this.suggestionsDropdown.style.display = 'none';
        }
        if (this.headerSuggestionsDropdown) {
            this.headerSuggestionsDropdown.style.display = 'none';
        }
        
        // Perform search with category filter
        this.currentFilters.category = categoryName;
        
        if (searchInput && searchInput.id === 'mainSearch') {
            this.transitionToSearchResults(categoryName);
        } else {
            this.currentPage = 1;
            this.performSearch(this.currentPage);
        }
    }

    selectBrandSuggestion(brandName) {
        const searchInput = document.getElementById('mainSearch');
        const headerSearch = document.getElementById('headerSearch');
        
        // Set the brand name as the search query
        if (searchInput) searchInput.value = brandName;
        if (headerSearch) headerSearch.value = brandName;
        
        this.currentQuery = brandName;
        if (this.suggestionsDropdown) {
            this.suggestionsDropdown.style.display = 'none';
        }
        if (this.headerSuggestionsDropdown) {
            this.headerSuggestionsDropdown.style.display = 'none';
        }
        
        // Perform search with brand filter
        this.currentFilters.brand = brandName;
        
        if (searchInput && searchInput.id === 'mainSearch') {
            this.transitionToSearchResults(brandName);
        } else {
            this.currentPage = 1;
            this.performSearch(this.currentPage);
        }
    }

    setupPriceRangeSlider() {
        const priceRangeSlider = document.getElementById('priceRangeSlider');
        
        if (!priceRangeSlider) return;

        try {
            noUiSlider.create(priceRangeSlider, {
                start: [0, 1000],
                connect: true,
                range: {
                    'min': 0,
                    'max': 1000
                },
                format: {
                    to: (value) => Math.round(value),
                    from: (value) => Number(value)
                }
            });

            // Update inputs when slider changes
            priceRangeSlider.noUiSlider.on('update', (values, handle) => {
                if (handle === 0) {
                    document.getElementById('minPrice').value = values[0];
                } else {
                    document.getElementById('maxPrice').value = values[1];
                }
            });

            // Update filters when slider changes
            priceRangeSlider.noUiSlider.on('change', (values) => {
                this.currentFilters.min_price = parseFloat(values[0]);
                this.currentFilters.max_price = parseFloat(values[1]);
                this.updateFilters();
            });
        } catch (error) {
            console.error('Error creating price range slider:', error);
        }
    }

    async performInitialSearch() {
        // Show some products by default instead of empty state
        try {
            const response = await fetch('/all-products?page=1&per_page=20');
            const data = await response.json();
            this.displayResults(data);
        } catch (error) {
            console.error('Error performing initial search:', error);
            this.showError('Failed to load products. Please refresh the page.');
        }
    }

    async performSearch(page = 1) {
        this.currentPage = page;
        this.showLoading(true);

        try {
            // Build query parameters
            const params = new URLSearchParams({
                page: page,
                per_page: this.perPage,
                type: 'products'
            });

            if (this.currentQuery) {
                params.append('q', this.currentQuery);
            }



            // Add sort parameter
            const sortSelect = document.getElementById('sortSelect');
            if (sortSelect && sortSelect.value) {
                params.append('sort', sortSelect.value);
            }

            // Add filters
            Object.entries(this.currentFilters).forEach(([key, value]) => {
                if (value !== undefined && value !== null && value !== '') {
                    params.append(key, value);
                }
            });

            const searchUrl = `/search?${params.toString()}`;
            console.log('Searching URL:', searchUrl);

            // Perform search
            const response = await fetch(searchUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Search response data:', data);

            // Update UI
            this.displayResults(data);
            this.updateSearchStats(data);

        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search failed. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(data) {
        const productGrid = document.getElementById('productGrid');
        const noResults = document.getElementById('noResults');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const resultsCount = document.getElementById('resultsCount');
        const resultsMeta = document.getElementById('resultsMeta');

        // Hide loading spinner
        this.showLoading(false);

        // Check if we have products
        if (!data || !data.products || data.products.length === 0) {
            // Show no results message
            if (productGrid) productGrid.innerHTML = '';
            if (noResults) {
                noResults.style.display = 'block';
                // Customize message based on search type
                const searchQuery = this.currentQuery || 'your search';
                noResults.innerHTML = `
                    <i class="fas fa-search"></i>
                    <h5>No products found</h5>
                    <p>No products match "${searchQuery}". Try different keywords or clear some filters.</p>
                    <button class="btn btn-primary mt-3" onclick="app.clearAllFilters()">Clear All Filters</button>
                `;
            }
            if (resultsCount) resultsCount.textContent = 'No results found';
            if (resultsMeta) resultsMeta.textContent = '';
            return;
        }

        // Hide no results message
        if (noResults) noResults.style.display = 'none';

        // Update results count and meta
        if (resultsCount) {
            resultsCount.textContent = `Found ${data.total} product${data.total !== 1 ? 's' : ''}`;
        }
        
        if (resultsMeta) {
            const executionTime = data.execution_time_ms ? ` in ${data.execution_time_ms}ms` : '';
            resultsMeta.textContent = `Page ${data.page} of ${data.total_pages}${executionTime}`;
        }

        // Build product grid
        let html = '';
        data.products.forEach(product => {
            html += this.createProductCard(product);
        });

        if (productGrid) {
            productGrid.innerHTML = html;
            productGrid.style.display = 'grid';
        } else {
            console.error('Product grid element not found!');
        }

        // Update pagination
        if (data.total_pages > 1) {
            this.updatePagination(data.page, data.total_pages);
        } else {
            const paginationContainer = document.getElementById('paginationContainer');
            if (paginationContainer) paginationContainer.innerHTML = '';
        }

        // Update search stats
        this.updateSearchStats(data);
        
        // Display category filter bar if category distribution is available
        if (data.category_distribution) {
            this.displayCategoryFilterBar(data.category_distribution);
        } else {
            // Hide category filter bar if no distribution data
            const categoryFilterBar = document.getElementById('categoryFilterBar');
            if (categoryFilterBar) {
                categoryFilterBar.style.display = 'none';
            }
        }
    }

    createProductCard(product) {
        // Validate and sanitize product data
        if (!product || !product.id) {
            console.error('Invalid product data:', product);
            return '';
        }

        let price = 'Price not available';
        let originalPrice = '';
        let discount = '';

        // Handle price display with better validation
        if (product.best_available_price) {
            // Aggregated product
            price = `€${parseFloat(product.best_available_price).toFixed(2)}`;
            if (product.min_price !== product.max_price) {
                price += ` - €${parseFloat(product.max_price).toFixed(2)}`;
            }
        } else if (product.price) {
            // Regular product
            if (typeof product.price === 'number') {
                price = `€${product.price.toFixed(2)}`;
            } else if (typeof product.price === 'string' && product.price.includes('€')) {
                price = product.price;
            } else {
                const numPrice = parseFloat(product.price);
                if (!isNaN(numPrice)) {
                    price = `€${numPrice.toFixed(2)}`;
                }
            }

            // Original price and discount
            if (product.original_price && product.original_price > parseFloat(product.price)) {
                originalPrice = `<del class="text-muted">€${parseFloat(product.original_price).toFixed(2)}</del>`;
                discount = `<span class="badge bg-warning text-dark ms-2">-${Math.round(((product.original_price - parseFloat(product.price)) / product.original_price) * 100)}%</span>`;
            }
        }

        // Handle availability with better logic
        let availability = '<span class="badge bg-secondary">Unknown</span>';
        if (product.availability === true || product.availability === 'true') {
            availability = '<span class="badge bg-success">Available</span>';
        } else if (product.availability === false || product.availability === 'false') {
            availability = '<span class="badge bg-danger">Out of Stock</span>';
        } else {
            // If availability is unknown, try to infer from stock quantity
            if (product.stock_quantity !== null && product.stock_quantity !== undefined && product.stock_quantity > 0) {
                availability = '<span class="badge bg-success">Available</span>';
            } else if (product.stock_quantity === 0) {
                availability = '<span class="badge bg-danger">Out of Stock</span>';
            }
        }
        
        // Handle stock information with better logic
        let stockInfo = '';
        if (product.stock_quantity !== null && product.stock_quantity !== undefined) {
            if (product.stock_quantity > 0) {
                stockInfo = `<small class="text-muted">Stock: ${product.stock_quantity} units</small>`;
            } else {
                stockInfo = '<small class="text-muted">Stock: Out of Stock</small>';
            }
        } else if (product.availability === true || product.availability === 'true') {
            stockInfo = '<small class="text-muted">Stock: Available</small>';
        } else if (product.availability === false || product.availability === 'false') {
            stockInfo = '<small class="text-muted">Stock: Out of Stock</small>';
        } else {
            stockInfo = '<small class="text-muted">Stock: Check Store</small>';
        }
        
        // Handle shop information
        let shopInfo = '';
        if (product.shop_count && product.shop_count > 0) {
            shopInfo = `<small class="text-muted">${product.shop_count} shops</small>`;
            // Add price comparison info if available
            if (product.price_comparison && product.shop_count > 1) {
                shopInfo += `<br><small class="text-info">Compare: ${product.price_comparison}</small>`;
            }
        } else if (product.shop) {
            const shopName = typeof product.shop === 'object' ? product.shop.name : product.shop;
            shopInfo = `<small class="text-muted">${shopName || 'Unknown Shop'}</small>`;
        }

        // Handle image URL with fallback
        const imageUrl = product.image_url && product.image_url !== 'https://via.placeholder.com/200x150?text=No+Image' 
            ? product.image_url 
            : 'https://via.placeholder.com/200x150?text=No+Image';
        
        // Handle brand and category names
        const brandName = product.brand ? (typeof product.brand === 'object' ? product.brand.name : product.brand) : '';
        const categoryName = product.category ? (typeof product.category === 'object' ? product.category.name : product.category) : '';
        
        // Sanitize title to prevent XSS
        const safeTitle = product.title ? product.title.replace(/[<>]/g, '') : 'Untitled Product';
        
        return `
            <div class="product-card" onclick="${product.shop_count > 1 ? `app.showProductComparison(${product.id})` : `app.showProductDetails(${product.id})`}">
                <img src="${imageUrl}" class="product-image" alt="${safeTitle}" onerror="this.src='https://via.placeholder.com/200x150?text=No+Image'">
                <div class="product-content">
                    <div class="product-meta mb-2">
                        ${brandName ? `<span class="badge bg-primary me-1">${brandName}</span>` : ''}
                        ${categoryName ? `<span class="badge bg-secondary">${categoryName}</span>` : ''}
                    </div>
                    <h6 class="product-title">${safeTitle}</h6>
                    <p class="product-description">${product.description ? product.description.substring(0, 100).replace(/[<>]/g, '') + '...' : ''}</p>
                    <div class="product-footer">
                        <div class="price-availability">
                            <div class="price">
                                <strong class="text-primary">${price}</strong>
                                ${originalPrice}
                                ${discount}
                            </div>
                            ${availability}
                        </div>
                        <div class="stock-info">
                            ${stockInfo}
                        </div>
                        <div class="shop-info">
                            ${shopInfo}
                            <button class="view-button" onclick="event.stopPropagation(); ${product.shop_count > 1 ? `app.showProductComparison(${product.id})` : `app.showProductDetails(${product.id})`}">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    updatePagination(currentPage, totalPages) {
        const paginationContainer = document.getElementById('paginationContainer');
        
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let paginationItems = '';

        // Previous button
        if (currentPage > 1) {
            paginationItems += `<li class="page-item"><a class="page-link" href="#" onclick="app.performSearch(${currentPage - 1})">‹</a></li>`;
        }

        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        if (startPage > 1) {
            paginationItems += `<li class="page-item"><a class="page-link" href="#" onclick="app.performSearch(1)">1</a></li>`;
            if (startPage > 2) {
                paginationItems += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            if (i === currentPage) {
                paginationItems += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                paginationItems += `<li class="page-item"><a class="page-link" href="#" onclick="app.performSearch(${i})">${i}</a></li>`;
            }
        }
        
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationItems += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationItems += `<li class="page-item"><a class="page-link" href="#" onclick="app.performSearch(${totalPages})">${totalPages}</a></li>`;
        }

        // Next button
        if (currentPage < totalPages) {
            paginationItems += `<li class="page-item"><a class="page-link" href="#" onclick="app.performSearch(${currentPage + 1})">›</a></li>`;
        }
        
        paginationContainer.innerHTML = `
            <nav aria-label="Search results pagination">
                <ul class="pagination justify-content-center">
                    ${paginationItems}
                </ul>
            </nav>
        `;
    }

    updateSearchStats(data) {
        const searchStats = document.getElementById('searchStats');
        if (data && data.total !== undefined) {
            const stats = `Found <span class="search-speed">${data.total.toLocaleString()}</span> results`;
            searchStats.innerHTML = stats;
            searchStats.style.display = 'block';
        } else {
            searchStats.style.display = 'none';
        }
    }

    async loadFacets() {
        try {
            const response = await fetch('/facets');
            const facets = await response.json();
            this.facetsData = facets;
            this.updateFacets(facets);
        } catch (error) {
            console.error('Error loading facets:', error);
        }
    }

    updateFacets(facets) {
        this.facetsData = facets;

        // Update price range slider
        if (facets.price_stats && facets.price_stats.min !== undefined) {
            const priceRangeSlider = document.getElementById('priceRangeSlider');
            if (priceRangeSlider && priceRangeSlider.noUiSlider) {
                const minPrice = Math.floor(facets.price_stats.min);
                const maxPrice = Math.ceil(facets.price_stats.max);

                priceRangeSlider.noUiSlider.updateOptions({
                    range: {
                        'min': minPrice,
                        'max': maxPrice
                    },
                    start: [
                        this.currentFilters.min_price || minPrice,
                        this.currentFilters.max_price || maxPrice
                    ]
                });
            }
        }

        // Update brand filters
        if (facets.brands) {
            this.updateBrandFilters(facets.brands);
        }

        // Update category filters
        if (facets.categories) {
            this.updateCategoryFilters(facets.categories);
        }
    }

    updateBrandFilters(brands) {
        const brandFiltersContainer = document.getElementById('brandFilters');
        if (!brandFiltersContainer) return;

        const html = brands.map(brand => `
            <div class="filter-item">
                <input type="checkbox" id="brand_${brand.name}" value="${brand.name}" 
                       ${this.currentFilters.brands && this.currentFilters.brands.includes(brand.name) ? 'checked' : ''}>
                <label for="brand_${brand.name}">${brand.name}</label>
                <span class="filter-count">${brand.count}</span>
            </div>
        `).join('');
        
        brandFiltersContainer.innerHTML = html;

        // Add event listeners
        brandFiltersContainer.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.handleBrandFilterChange();
            });
        });
    }

    updateCategoryFilters(categories) {
        const categoryFiltersContainer = document.getElementById('categoryFilters');
        if (!categoryFiltersContainer) return;

        const html = categories.map(category => `
            <div class="filter-item">
                <input type="checkbox" id="category_${category.name}" value="${category.name}" 
                       ${this.currentFilters.categories && this.currentFilters.categories.includes(category.name) ? 'checked' : ''}>
                <label for="category_${category.name}">${category.name}</label>
                <span class="filter-count">${category.count}</span>
            </div>
        `).join('');
        
        categoryFiltersContainer.innerHTML = html;

        // Add event listeners
        categoryFiltersContainer.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.handleCategoryFilterChange();
            });
        });
    }

    handleBrandFilterChange() {
        const brandCheckboxes = document.querySelectorAll('#brandFilters input[type="checkbox"]:checked');
        this.currentFilters.brands = Array.from(brandCheckboxes).map(cb => cb.value);
        this.updateFilters();
    }

    handleCategoryFilterChange() {
        const categoryCheckboxes = document.querySelectorAll('#categoryFilters input[type="checkbox"]:checked');
        this.currentFilters.categories = Array.from(categoryCheckboxes).map(cb => cb.value);
        this.updateFilters();
    }

    filterBrandOptions(searchTerm) {
        const brandItems = document.querySelectorAll('#brandFilters .filter-item');
        brandItems.forEach(item => {
            const label = item.querySelector('label').textContent.toLowerCase();
            if (label.includes(searchTerm.toLowerCase())) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    filterCategoryOptions(searchTerm) {
        const categoryItems = document.querySelectorAll('#categoryFilters .filter-item');
        categoryItems.forEach(item => {
            const label = item.querySelector('label').textContent.toLowerCase();
            if (label.includes(searchTerm.toLowerCase())) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    // Category Filter Bar Methods
    displayCategoryFilterBar(categoryDistribution) {
        const categoryFilterBar = document.getElementById('categoryFilterBar');
        const categoryFilterScroll = document.getElementById('categoryFilterScroll');
        const clearCategoryFilters = document.getElementById('clearCategoryFilters');
        
        if (!categoryDistribution || categoryDistribution.length === 0) {
            categoryFilterBar.style.display = 'none';
            return;
        }
        
        // Add "All Categories" button
        const allCategoriesButton = `
            <button class="category-filter-btn ${!this.currentFilters.categories ? 'active' : ''}" 
                    onclick="app.clearCategoryFilters()">
                <span class="category-name">All Categories</span>
            </button>
        `;
        
        // Create category cards - limit to 12 maximum
        const limitedCategories = categoryDistribution.slice(0, 12); // Limit to 12 categories
        const categoryCards = limitedCategories.map(category => {
            const isActive = this.currentFilters.categories && 
                           this.currentFilters.categories.includes(category.category_name);
            const imageUrl = category.representative_image || '';
            const displayName = category.category_name_en || category.category_name;
            const productCount = category.count || 0;
            
            console.log(`Category: ${displayName}, Image: ${imageUrl}, Count: ${productCount}`); // Debug log
            
            return `
                <div class="category-filter-card ${isActive ? 'active' : ''}" 
                     onclick="app.toggleCategoryFilter('${category.category_name}')"
                     data-category-name="${category.category_name}">
                    <div class="category-filter-card-image">
                        ${imageUrl ? `<img src="${imageUrl}" alt="${displayName}" onerror="this.handleImageError(this, '${displayName}');" onload="console.log('Image loaded:', '${imageUrl}');" crossorigin="anonymous" />` : displayName}
                    </div>
                    <div class="category-filter-card-name">
                        ${displayName}
                        <div class="category-filter-card-count">
                            ${productCount} product${productCount !== 1 ? 's' : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        categoryFilterScroll.innerHTML = allCategoriesButton + categoryCards;
        categoryFilterBar.style.display = 'block';
        
        // Show/hide clear button based on active filters
        const hasActiveCategories = this.currentFilters.categories && 
                                  this.currentFilters.categories.length > 0;
        clearCategoryFilters.style.display = hasActiveCategories ? 'block' : 'none';
    }

    toggleCategoryFilter(categoryName) {
        // Single selection only - replace current category
        if (this.currentFilters.categories && this.currentFilters.categories.includes(categoryName)) {
            // If clicking the same category, clear it completely
            delete this.currentFilters.categories;
        } else {
            // Select this category (single selection)
            this.currentFilters.categories = [categoryName];
        }
        
        // Update UI
        this.updateCategoryFilterButtons();
        this.updateFilters();
    }

    updateCategoryFilterButtons() {
        const categoryButtons = document.querySelectorAll('.category-filter-btn');
        const categoryCards = document.querySelectorAll('.category-filter-card');
        const clearCategoryFilters = document.getElementById('clearCategoryFilters');
        
        // Update category cards
        categoryCards.forEach(card => {
            const categoryName = card.getAttribute('data-category-name');
            if (categoryName) {
                const isActive = this.currentFilters.categories && 
                               this.currentFilters.categories.includes(categoryName);
                
                if (isActive) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
            }
        });
        
        // Update "All Categories" button state
        const allCategoriesButton = document.querySelector('.category-filter-btn:not([data-category-name])');
        if (allCategoriesButton) {
            if (!this.currentFilters.categories) {
                allCategoriesButton.classList.add('active');
            } else {
                allCategoriesButton.classList.remove('active');
            }
        }
        
        // Show/hide clear button
        const hasActiveCategories = this.currentFilters.categories && 
                                  this.currentFilters.categories.length > 0;
        clearCategoryFilters.style.display = hasActiveCategories ? 'block' : 'none';
    }

    clearCategoryFilters() {
        // Completely remove categories filter instead of setting empty array
        delete this.currentFilters.categories;
        this.updateCategoryFilterButtons();
        this.updateFilters();
    }

    handleImageError(img, displayName) {
        console.log('Image failed to load:', img.src);
        img.style.display = 'none';
        img.parentElement.innerHTML = displayName;
    }





    updateFilters() {
        // Clean up empty categories before sending to server
        if (this.currentFilters.categories && this.currentFilters.categories.length === 0) {
            delete this.currentFilters.categories;
        }
        
        this.updateActiveFilters();
        this.currentPage = 1;
        this.performSearch(this.currentPage);
    }

    updateActiveFilters() {
        const activeFilters = [];

        if (this.currentFilters.availability) {
            activeFilters.push({
                type: 'availability',
                value: this.currentFilters.availability,
                label: 'Available only'
            });
        }

        if (this.currentFilters.min_price || this.currentFilters.max_price) {
            const minPrice = this.currentFilters.min_price || 0;
            const maxPrice = this.currentFilters.max_price || '∞';
            activeFilters.push({
                type: 'price',
                value: 'price',
                label: `Price: €${minPrice} - €${maxPrice}`
            });
        }

        if (this.currentFilters.brands && this.currentFilters.brands.length > 0) {
            this.currentFilters.brands.forEach(brand => {
                activeFilters.push({
                    type: 'brand',
                    value: brand,
                    label: `Brand: ${brand}`
                });
            });
        }

        if (this.currentFilters.categories && this.currentFilters.categories.length > 0) {
            this.currentFilters.categories.forEach(category => {
                activeFilters.push({
                    type: 'category',
                    value: category,
                    label: `Category: ${category}`
                });
            });
        }

        const activeFiltersContainer = document.getElementById('activeFilters');
        activeFiltersContainer.innerHTML = activeFilters.map(filter => `
            <div class="filter-tag">
                ${filter.label}
                <span class="remove" onclick="app.removeFilter('${filter.type}', '${filter.value}')">×</span>
            </div>
        `).join('');
    }

    removeFilter(type, value) {
        switch (type) {
            case 'availability':
                delete this.currentFilters.availability;
                break;
            case 'price':
                delete this.currentFilters.min_price;
                delete this.currentFilters.max_price;
                break;
            case 'brand':
                if (this.currentFilters.brands) {
                    this.currentFilters.brands = this.currentFilters.brands.filter(b => b !== value);
                    if (this.currentFilters.brands.length === 0) {
                        delete this.currentFilters.brands;
                    }
                }
                // Update checkbox
                const brandCheckbox = document.getElementById(`brand_${value}`);
                if (brandCheckbox) brandCheckbox.checked = false;
                break;
            case 'category':
                if (this.currentFilters.categories) {
                    this.currentFilters.categories = this.currentFilters.categories.filter(c => c !== value);
                    if (this.currentFilters.categories.length === 0) {
                        delete this.currentFilters.categories;
                    }
                }
                // Update checkbox
                const categoryCheckbox = document.getElementById(`category_${value}`);
                if (categoryCheckbox) categoryCheckbox.checked = false;
                break;
        }

        this.updateFilters();
    }

    clearAllFilters() {
        this.currentFilters = {};

        // Reset form elements
        document.querySelectorAll('.filter-option input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Clear brand and category checkboxes
        document.querySelectorAll('#brandFilters input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        document.querySelectorAll('#categoryFilters input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Clear price inputs
        document.getElementById('minPrice').value = '';
        document.getElementById('maxPrice').value = '';

        // Reset price slider
        const priceRangeSlider = document.getElementById('priceRangeSlider');
        if (priceRangeSlider && priceRangeSlider.noUiSlider && this.facetsData.price_stats) {
            priceRangeSlider.noUiSlider.set([
                this.facetsData.price_stats.min,
                this.facetsData.price_stats.max
            ]);
        }

        this.updateFilters();
    }

    async showProductDetails(productId) {
        try {
            console.log('Show product details for:', productId);

            // Validate product ID
            if (!productId || isNaN(productId)) {
                console.error('Invalid product ID:', productId);
                this.showError('Invalid product ID');
                return;
            }

            // Get modal element
            const modalElement = document.getElementById('productModal');
            const modalBody = document.getElementById('productModalBody');

            if (!modalElement || !modalBody) {
                console.error('Modal elements not found');
                this.showError('Modal elements not found');
                return;
            }

            // Show loading state
            modalBody.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading product details...</p>
                </div>
            `;

            // Show modal with proper Bootstrap handling
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
            // Add event listener for modal close
            modalElement.addEventListener('hidden.bs.modal', () => {
                this.closeModal();
            });

            // Try to get product details from API
            let product = null;
            try {
                const response = await fetch(`/product/${productId}`);
                if (response.ok) {
                    product = await response.json();
                } else {
                    console.warn(`API returned status ${response.status} for product ${productId}`);
                }
            } catch (error) {
                console.log('API endpoint not available, using search data');
            }

            // Display product details
            if (product) {
                this.displayProductModal(product);
            } else {
                modalBody.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Product details not available. The product may have been removed or the data is temporarily unavailable.
                    </div>
                    <div class="text-center mt-3">
                        <button class="btn btn-secondary" onclick="app.closeModal()">Close</button>
                    </div>
                `;
            }

        } catch (error) {
            console.error('Error showing product details:', error);
            const modalBody = document.getElementById('productModalBody');
            if (modalBody) {
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Error loading product details: ${error.message}
                    </div>
                    <div class="text-center mt-3">
                        <button class="btn btn-secondary" onclick="app.closeModal()">Close</button>
                    </div>
                `;
            }
        }
    }

    async showProductComparison(productId) {
        try {
            console.log('Show product comparison for:', productId);

            // Validate product ID
            if (!productId || isNaN(productId)) {
                console.error('Invalid product ID:', productId);
                this.showError('Invalid product ID');
                return;
            }

            // Get modal element
            const modalElement = document.getElementById('productModal');
            const modalBody = document.getElementById('productModalBody');

            if (!modalElement || !modalBody) {
                console.error('Modal elements not found');
                this.showError('Modal elements not found');
                return;
            }

            // Check if modal is already open with the same product
            if (modalElement.classList.contains('show') && this.currentComparisonProductId === productId) {
                console.log('Comparison modal already open for this product');
                return;
            }

            // Store current comparison product ID
            this.currentComparisonProductId = productId;

            // Show loading state
            modalBody.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading product comparison...</p>
                </div>
            `;

            // Show modal with proper Bootstrap handling
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
            // Add event listener for modal close (only once)
            if (!this.modalCloseListenerAdded) {
                modalElement.addEventListener('hidden.bs.modal', () => {
                    this.closeModal();
                    this.currentComparisonProductId = null;
                });
                this.modalCloseListenerAdded = true;
            }

            // Try to get product comparison from API
            let comparisonData = null;
            try {
                const response = await fetch(`/product/${productId}/comparison`);
                if (response.ok) {
                    comparisonData = await response.json();
                } else {
                    console.warn(`API returned status ${response.status} for product comparison ${productId}`);
                }
            } catch (error) {
                console.log('API endpoint not available, using search data');
            }

            // Display product comparison
            if (comparisonData) {
                this.displayProductComparisonModal(comparisonData);
            } else {
                modalBody.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Product comparison not available. The product may have been removed or the data is temporarily unavailable.
                    </div>
                    <div class="text-center mt-3">
                        <button class="btn btn-secondary" onclick="app.closeModal()">Close</button>
                    </div>
                `;
            }

        } catch (error) {
            console.error('Error showing product comparison:', error);
            const modalBody = document.getElementById('productModalBody');
            if (modalBody) {
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Error loading product comparison: ${error.message}
                    </div>
                    <div class="text-center mt-3">
                        <button class="btn btn-secondary" onclick="app.closeModal()">Close</button>
                    </div>
                `;
            }
        }
    }

    displayProductModal(product) {
        const modalBody = document.getElementById('productModalBody');
        const modalTitle = document.getElementById('productModalLabel');
        const modalElement = document.getElementById('productModal');

        if (!modalBody || !modalTitle || !modalElement) {
            console.error('Modal elements not found');
            return;
        }

        // Validate product data
        if (!product || !product.title) {
            modalBody.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Invalid product data
                </div>
            `;
            return;
        }

        modalTitle.textContent = product.title || 'Product Details';

        // Handle image URL with validation
        const imageUrl = product.image_url && product.image_url !== 'https://via.placeholder.com/200x150?text=No+Image' 
            ? product.image_url 
            : null;

        // Handle price with better validation
        let price = 'Price not available';
        if (product.price) {
            if (typeof product.price === 'string' && product.price.includes('€')) {
                price = product.price;
            } else {
                const numPrice = parseFloat(product.price);
                if (!isNaN(numPrice)) {
                    price = `€${numPrice.toFixed(2)}`;
                }
            }
        }

        // Handle original price and discount
        let originalPrice = '';
        let discount = '';
        if (product.original_price && product.original_price > parseFloat(product.price || 0)) {
            originalPrice = `<del class="text-muted ms-2">€${parseFloat(product.original_price).toFixed(2)}</del>`;
            const discountPercent = Math.round(((product.original_price - parseFloat(product.price || 0)) / product.original_price) * 100);
            discount = `<span class="badge bg-warning text-dark ms-2">-${discountPercent}%</span>`;
        }

        // Handle availability with better logic
        let availability = '<span class="badge bg-secondary">Unknown</span>';
        if (product.availability === true || product.availability === 'true') {
            availability = '<span class="badge bg-success">Available</span>';
        } else if (product.availability === false || product.availability === 'false') {
            availability = '<span class="badge bg-danger">Out of Stock</span>';
        }

        // Sanitize all text content
        const safeTitle = product.title ? product.title.replace(/[<>]/g, '') : 'Untitled Product';
        const safeDescription = product.description ? product.description.replace(/[<>]/g, '') : '';

        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-5">
                    ${imageUrl ? 
                        `<img src="${imageUrl}" class="img-fluid rounded" alt="${safeTitle}" style="width: 100%; max-height: 300px; object-fit: contain;" onerror="this.src='https://via.placeholder.com/300x300?text=No+Image'">` :
                        `<div class="bg-light rounded d-flex align-items-center justify-content-center" style="height: 300px;">
                            <i class="fas fa-image fa-3x text-muted"></i>
                        </div>`
                    }
                </div>
                <div class="col-md-7">
                    <h5 class="mb-3">${safeTitle}</h5>

                    ${safeDescription ? `<p class="text-muted mb-3">${safeDescription}</p>` : ''}

                    <div class="mb-3">
                        <h4 class="text-primary mb-1">
                            ${price}
                            ${originalPrice}
                            ${discount}
                        </h4>
                    </div>

                    <div class="mb-3">
                        <strong>Availability:</strong> ${availability}
                    </div>
                        
                    ${product.stock_quantity !== null && product.stock_quantity !== undefined ? `
                        <div class="mb-3">
                            <strong>Stock:</strong> ${product.stock_quantity > 0 ? `${product.stock_quantity} units` : 'Out of Stock'}
                        </div>
                    ` : ''}
                        
                    ${product.brand ? `
                        <div class="mb-3">
                            <strong>Brand:</strong> ${typeof product.brand === 'object' ? product.brand.name : product.brand}
                        </div>
                    ` : ''}
                        
                    ${product.shop ? `
                        <div class="mb-3">
                            <strong>Shop:</strong> ${typeof product.shop === 'object' ? product.shop.name : product.shop}
                        </div>
                    ` : ''}
                        
                    ${product.category ? `
                        <div class="mb-3">
                            <strong>Category:</strong> ${typeof product.category === 'object' ? product.category.name : product.category}
                        </div>
                    ` : ''}

                    ${product.ean ? `
                        <div class="mb-3">
                            <strong>EAN:</strong> ${product.ean}
                        </div>
                    ` : ''}

                    ${product.mpn ? `
                        <div class="mb-3">
                            <strong>MPN:</strong> ${product.mpn}
                        </div>
                    ` : ''}
                        
                    ${product.product_url ? `
                        <div class="mt-4">
                            <a href="${product.product_url}" target="_blank" class="btn btn-primary">
                                <i class="fas fa-external-link-alt me-2"></i>
                                View on Store
                            </a>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    displayProductComparisonModal(comparisonData) {
        const modalBody = document.getElementById('productModalBody');
        const modalTitle = document.getElementById('productModalLabel');
        const modalElement = document.getElementById('productModal');

        if (!modalBody || !modalTitle || !modalElement) {
            console.error('Modal elements not found');
            return;
        }

        // Validate comparison data
        if (!comparisonData || !comparisonData.products || comparisonData.products.length === 0) {
            modalBody.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    No comparison data available.
                </div>
                <div class="text-center mt-3">
                    <button class="btn btn-secondary" onclick="app.closeModal()">Close</button>
                </div>
            `;
            return;
        }

        // Set modal title
        modalTitle.textContent = `Compare: ${comparisonData.title || 'Product Comparison'}`;

        // Create comparison table layout for better attribute comparison
        let comparisonHTML = `
            <div class="product-comparison">
                <div class="comparison-header mb-3">
                    <h5 class="text-center">${comparisonData.title || 'Product Comparison'}</h5>
                    <p class="text-muted text-center">Compare prices and details across ${comparisonData.total_shops || comparisonData.products.length} shops (${comparisonData.available_count || 0} available)</p>
                </div>
                
                <!-- Summary Cards -->
                <div class="comparison-summary mb-4">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="summary-card text-center p-3 border rounded">
                                <div class="text-success fw-bold fs-4">€${comparisonData.best_price?.toFixed(2) || '0.00'}</div>
                                <small class="text-muted">Best Price</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="summary-card text-center p-3 border rounded">
                                <div class="text-primary fw-bold fs-4">€${comparisonData.min_price?.toFixed(2) || '0.00'}</div>
                                <small class="text-muted">Lowest Price</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="summary-card text-center p-3 border rounded">
                                <div class="text-info fw-bold fs-4">€${comparisonData.max_price?.toFixed(2) || '0.00'}</div>
                                <small class="text-muted">Highest Price</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="summary-card text-center p-3 border rounded">
                                <div class="text-warning fw-bold fs-4">${comparisonData.available_count || 0}</div>
                                <small class="text-muted">Available in ${comparisonData.total_shops || comparisonData.products.length} shops</small>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Comparison Table -->
                <div class="comparison-table-container">
                    <div class="table-responsive">
                        <table class="table table-bordered comparison-table">
                            <thead class="table-light">
                                <tr>
                                    <th style="width: 200px;">Attribute</th>
                                    ${comparisonData.products.map(product => `
                                        <th class="text-center" style="min-width: 200px;">
                                            <div class="shop-header">
                                                <div class="shop-name fw-bold">${product.shop_name}</div>
                                                ${product.price === comparisonData.best_price ? 
                                                    '<span class="badge bg-success">Best Price</span>' : ''
                                                }
                                            </div>
                                        </th>
                                    `).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Product Images -->
                                <tr>
                                    <td class="fw-bold">Product Image</td>
                                    ${comparisonData.products.map(product => `
                                        <td class="text-center">
                                            <img src="${product.image_url || 'https://via.placeholder.com/120x120?text=No+Image'}" 
                                                 alt="${product.title}" 
                                                 class="img-fluid rounded"
                                                 style="max-height: 120px;"
                                                 onerror="this.src='https://via.placeholder.com/120x120?text=No+Image'">
                                        </td>
                                    `).join('')}
                                </tr>
                                
                                <!-- Product Title -->
                                <tr>
                                    <td class="fw-bold">Product Title</td>
                                    ${comparisonData.products.map(product => `
                                        <td>
                                            <div class="product-title">${product.title}</div>
                                        </td>
                                    `).join('')}
                                </tr>
                                
                                <!-- Price -->
                                <tr>
                                    <td class="fw-bold">Price</td>
                                    ${comparisonData.products.map(product => `
                                        <td class="text-center">
                                            <div class="price ${product.price === comparisonData.best_price ? 'text-success fw-bold fs-5' : 'text-primary fw-bold'}">
                                                €${parseFloat(product.price).toFixed(2)}
                                            </div>
                                        </td>
                                    `).join('')}
                                </tr>
                                
                                <!-- Availability -->
                                <tr>
                                    <td class="fw-bold">Availability</td>
                                    ${comparisonData.products.map(product => `
                                        <td class="text-center">
                                            ${product.availability ? 
                                                '<span class="badge bg-success">In Stock</span>' : 
                                                '<span class="badge bg-danger">Out of Stock</span>'
                                            }
                                        </td>
                                    `).join('')}
                                </tr>
                                
                                <!-- Brand -->
                                <tr>
                                    <td class="fw-bold">Brand</td>
                                    ${comparisonData.products.map(product => `
                                        <td class="text-center">
                                            ${product.brand_name || '<span class="text-muted">Not specified</span>'}
                                        </td>
                                    `).join('')}
                                </tr>
                                
                                <!-- Category -->
                                <tr>
                                    <td class="fw-bold">Category</td>
                                    ${comparisonData.products.map(product => `
                                        <td class="text-center">
                                            ${product.category_name || '<span class="text-muted">Not specified</span>'}
                                        </td>
                                    `).join('')}
                                </tr>
                                
                                <!-- EAN -->
                                <tr>
                                    <td class="fw-bold">EAN Code</td>
                                    ${comparisonData.products.map(product => `
                                        <td class="text-center">
                                            ${product.ean || '<span class="text-muted">Not specified</span>'}
                                        </td>
                                    `).join('')}
                                </tr>
                                
                                <!-- MPN -->
                                <tr>
                                    <td class="fw-bold">MPN</td>
                                    ${comparisonData.products.map(product => `
                                        <td class="text-center">
                                            ${product.mpn || '<span class="text-muted">Not specified</span>'}
                                        </td>
                                    `).join('')}
                                </tr>
                                
                                <!-- Description -->
                                <tr>
                                    <td class="fw-bold">Description</td>
                                    ${comparisonData.products.map(product => `
                                        <td>
                                            <div class="product-description">
                                                ${product.description ? 
                                                    (product.description.length > 150 ? 
                                                        product.description.substring(0, 150) + '...' : 
                                                        product.description
                                                    ) : 
                                                    '<span class="text-muted">No description available</span>'
                                                }
                                            </div>
                                        </td>
                                    `).join('')}
                                </tr>
                                
                                <!-- Actions -->
                                <tr>
                                    <td class="fw-bold">Actions</td>
                                    ${comparisonData.products.map(product => `
                                        <td class="text-center">
                                            <div class="action-buttons">
                                                <button class="btn btn-primary btn-sm mb-1" onclick="app.showProductDetails(${product.id})">
                                                    <i class="fas fa-eye"></i> Details
                                                </button>
                                                ${product.url ? `
                                                    <button class="btn btn-outline-success btn-sm mb-1" onclick="window.open('${product.url}', '_blank')">
                                                        <i class="fas fa-external-link-alt"></i> Visit Shop
                                                    </button>
                                                ` : ''}
                                            </div>
                                        </td>
                                    `).join('')}
                                </tr>
                                
                                <!-- Summary Row -->
                                <tr class="table-info">
                                    <td class="fw-bold">Summary</td>
                                    <td colspan="${comparisonData.products.length}" class="text-center">
                                        <div class="row">
                                            <div class="col-md-4">
                                                <strong>Total Shops:</strong> ${comparisonData.total_shops || comparisonData.products.length}
                                            </div>
                                            <div class="col-md-4">
                                                <strong>Available:</strong> ${comparisonData.available_count || 0}
                                            </div>
                                            <div class="col-md-4">
                                                <strong>Price Range:</strong> €${comparisonData.min_price?.toFixed(2) || '0.00'} - €${comparisonData.max_price?.toFixed(2) || '0.00'}
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        modalBody.innerHTML = comparisonHTML;
    }

    closeModal() {
        const modalElement = document.getElementById('productModal');
        
        if (modalElement) {
            // Use Bootstrap modal API to close properly
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            } else {
                // Fallback to manual close
                modalElement.style.display = 'none';
                modalElement.classList.remove('show');
                
                // Remove backdrop
                const backdrop = document.getElementById('modalBackdrop');
                if (backdrop) {
                    backdrop.remove();
                }
                
                document.body.classList.remove('modal-open');
            }
        }
        
        // Return focus to the page
        document.body.focus();
    }

    showLoading(show) {
        const loadingSpinner = document.getElementById('loadingSpinner');
        const productGrid = document.getElementById('productGrid');
        
        if (show) {
            loadingSpinner.style.display = 'block';
            productGrid.style.display = 'none';
            document.getElementById('noResults').style.display = 'none';
        } else {
            loadingSpinner.style.display = 'none';
        }
    }

    showNoResults() {
        const productGrid = document.getElementById('productGrid');
        productGrid.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No products found matching your criteria.
                </div>
            `;
        document.getElementById('noResults').style.display = 'none';
        productGrid.style.display = 'block';
    }

    showError(message) {
        console.error(message);
        this.showLoading(false);
        document.getElementById('resultsCount').textContent = 'Search error';
        document.getElementById('resultsMeta').textContent = message;
        this.showNoResults();
    }

    startVoiceInput(searchInput) {
        const voiceBtn = searchInput.id === 'mainSearch' ? 
            document.getElementById('voiceBtn') : 
            document.getElementById('voiceBtnHeader');

        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            alert('Speech recognition is not supported in this browser.');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();

        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        // Add recording class to button
        voiceBtn.classList.add('recording');
        voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';

        recognition.onstart = () => {
            console.log('Voice recognition started');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            searchInput.value = transcript;
            this.currentQuery = transcript;
            
            // Auto-search after voice input
            if (searchInput.id === 'mainSearch') {
                this.transitionToSearchResults(transcript);
            } else {
                this.currentPage = 1;
                this.performSearch(this.currentPage);
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            alert('Voice recognition error: ' + event.error);
        };

        recognition.onend = () => {
            // Remove recording class from button
            voiceBtn.classList.remove('recording');
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        };

        recognition.start();
    }

    startImageInput(searchInput) {
        // Create a hidden file input
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.style.display = 'none';

        fileInput.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                this.processImageSearch(file, searchInput);
            }
        });

        // Trigger file selection
        fileInput.click();
    }

    async processImageSearch(file, searchInput) {
        try {
            // Show loading state
            const imageBtn = searchInput.id === 'mainSearch' ? 
                document.getElementById('imageBtn') : 
                document.getElementById('imageBtnHeader');
            
            const originalContent = imageBtn.innerHTML;
            imageBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

            // Create FormData for file upload
            const formData = new FormData();
            formData.append('image', file);

            // Upload image and get search results
            const response = await fetch('/image-search', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                
                // Set search input with detected text or suggested search
                const searchText = result.search_query || result.description || 'image search';
                searchInput.value = searchText;
                this.currentQuery = searchText;

                // Auto-search after image input
                if (searchInput.id === 'mainSearch') {
                    this.transitionToSearchResults(searchText);
                } else {
                    this.currentPage = 1;
                    this.performSearch(this.currentPage);
                }
            } else {
                throw new Error('Image search failed');
            }

        } catch (error) {
            console.error('Image search error:', error);
            alert('Image search failed. Please try again.');
        } finally {
            // Restore button content
            const imageBtn = searchInput.id === 'mainSearch' ? 
                document.getElementById('imageBtn') : 
                document.getElementById('imageBtnHeader');
            imageBtn.innerHTML = '<i class="fas fa-camera"></i>';
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.app = new ProductSearchApp();
});
