class ModernSearchApp {
    constructor() {
        console.log('ModernSearchApp constructor called');
        // Initialize immediately
        this.initializeElements();
        this.init();
    }

    initializeElements() {
        console.log('Initializing elements...');
        this.searchInput = document.getElementById('mainSearch');
        this.searchBtn = document.getElementById('searchBtn');
        this.suggestionsDropdown = document.getElementById('suggestionsDropdown');
        this.productGrid = document.getElementById('productGrid');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.noResults = document.getElementById('noResults');
        this.resultsCount = document.getElementById('resultsCount');
        this.resultsMeta = document.getElementById('resultsMeta');
        this.searchStats = document.getElementById('searchStats');
        this.categoryResults = document.getElementById('categoryResults');
        this.categoryList = document.getElementById('categoryList');
        this.paginationContainer = document.getElementById('paginationContainer');

        // Filter elements
        this.filterSidebar = document.getElementById('filterSidebar');
        this.brandFilters = document.getElementById('brandFilters');
        this.categoryFilters = document.getElementById('categoryFilters');
        this.shopFilters = document.getElementById('shopFilters');
        this.activeFilters = document.getElementById('activeFilters');
        this.clearFiltersBtn = document.getElementById('clearFilters');

        // Mobile elements
        this.mobileFilterBtn = document.getElementById('mobileFilterBtn');
        this.filterBackdrop = document.getElementById('filterBackdrop');
        this.closeMobileFilters = document.getElementById('closeMobileFilters');

        // Price range
        this.priceRangeSlider = null;
        this.minPriceInput = document.getElementById('minPrice');
        this.maxPriceInput = document.getElementById('maxPrice');

        // State
        this.currentQuery = '';
        this.currentPage = 1;
        this.currentFilters = {};
        this.facetsData = {};
        this.suggestionTimeout = null;
        this.lastSearchTime = 0;

        // Filter pagination state
        this.brandFilterPage = 1;
        this.categoryFilterPage = 1;
        this.itemsPerFilterPage = 12;
        
        console.log('Elements initialized:', {
            searchInput: !!this.searchInput,
            productGrid: !!this.productGrid,
            resultsContainer: !!this.resultsContainer
        });
    }

    init() {
        this.setupEventListeners();
        this.setupPriceRangeSlider();
        this.initializeLanguage();
        this.loadInitialData();
        this.performInitialSearch();
    }

    initializeLanguage() {
        // Set English as default language
        document.getElementById('languageSelect').value = 'el';
        this.switchLanguage('el');
    }

    switchLanguage(lang) {
        // Update all elements with language data attributes
        document.querySelectorAll('[data-text-el][data-text-en]').forEach(element => {
            if (lang === 'el') {
                element.textContent = element.getAttribute('data-text-el');
            } else {
                element.textContent = element.getAttribute('data-text-en');
            }
        });

        // Update placeholders
        const searchInput = document.getElementById('mainSearch');
        if (lang === 'el') {
            searchInput.placeholder = searchInput.getAttribute('data-placeholder-el');
        } else {
            searchInput.placeholder = searchInput.getAttribute('data-placeholder-en');
        }

        // Update HTML lang attribute
        document.documentElement.lang = lang;
    }

    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Search functionality
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                console.log('Search input event:', e.target.value);
                this.handleSearchInput(e.target.value);
            });

            this.searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    console.log('Search Enter pressed');
                    this.currentPage = 1;
                    this.performSearch(this.currentPage);
                }
            });
        }

        if (this.searchBtn) {
            this.searchBtn.addEventListener('click', () => {
                console.log('Search button clicked');
                this.currentPage = 1;
                this.performSearch(this.currentPage);
            });
        }

        // Suggestions dropdown
        if (this.searchInput) {
            this.searchInput.addEventListener('focus', () => {
                if (this.suggestionsDropdown && this.suggestionsDropdown.children.length > 0) {
                    this.suggestionsDropdown.style.display = 'block';
                }
            });
        }

        document.addEventListener('click', (e) => {
            if (this.searchInput && this.suggestionsDropdown && 
                !this.searchInput.contains(e.target) && !this.suggestionsDropdown.contains(e.target)) {
                this.suggestionsDropdown.style.display = 'none';
            }
        });

        // Filter functionality
        if (this.clearFiltersBtn) {
            this.clearFiltersBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }

        // Mobile filter controls
        if (this.mobileFilterBtn) {
            this.mobileFilterBtn.addEventListener('click', () => {
                this.showMobileFilters();
            });
        }

        if (this.filterBackdrop) {
            this.filterBackdrop.addEventListener('click', () => {
                this.hideMobileFilters();
            });
        }

        if (this.closeMobileFilters) {
            this.closeMobileFilters.addEventListener('click', () => {
                this.hideMobileFilters();
            });
        }

        // Price range inputs
        if (this.minPriceInput) {
            this.minPriceInput.addEventListener('change', () => {
                this.updateFilters();
            });
        }

        if (this.maxPriceInput) {
            this.maxPriceInput.addEventListener('change', () => {
                this.updateFilters();
            });
        }

        // Sort functionality
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.currentFilters.sort = e.target.value;
                this.currentPage = 1;
                this.performSearch(this.currentPage);
            });
        }

        // Language selector
        const languageSelect = document.getElementById('languageSelect');
        if (languageSelect) {
            languageSelect.addEventListener('change', (e) => {
                this.switchLanguage(e.target.value);
            });
        }

        // Availability filters
        const availableOnly = document.getElementById('availableOnly');
        if (availableOnly) {
            availableOnly.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.currentFilters.availability = true;
                } else {
                    delete this.currentFilters.availability;
                }
                this.updateFilters();
            });
        }

        const inStock = document.getElementById('inStock');
        if (inStock) {
            inStock.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.currentFilters.stock = true;
                } else {
                    delete this.currentFilters.stock;
                }
                this.updateFilters();
            });
        }
        
        console.log('Event listeners set up successfully');
    }

    setupPriceRangeSlider() {
        const priceRangeSlider = document.getElementById('priceRangeSlider');
        
        if (!priceRangeSlider) {
            console.log('Price range slider not found');
            return;
        }

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
                },
                cssPrefix: 'noUi-',
                cssClasses: {
                    target: 'target',
                    base: 'base',
                    origin: 'origin',
                    handle: 'handle',
                    horizontal: 'horizontal',
                    vertical: 'vertical',
                    background: 'background',
                    connect: 'connect',
                    connects: 'connects',
                    tooltip: 'tooltip',
                    tooltips: 'tooltips',
                    pips: 'pips',
                    pip: 'pip',
                    value: 'value'
                }
            });

            this.priceRangeSlider = priceRangeSlider;

            // Update inputs when slider changes
            priceRangeSlider.noUiSlider.on('update', (values, handle) => {
                if (handle === 0) {
                    this.minPriceInput.value = values[0];
                } else {
                    this.maxPriceInput.value = values[1];
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

    async loadInitialData() {
        try {
            // Load facets for filters
            await this.loadFacets();
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    async performInitialSearch() {
        this.showLoading(true);
        await this.performSearch();
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
            this.suggestionsDropdown.style.display = 'none';
        }
    }

    async getSuggestions(query) {
        try {
            const response = await fetch(`/suggestions?q=${encodeURIComponent(query)}&limit=8`);
            const suggestions = await response.json();

            this.displaySuggestions(suggestions);
        } catch (error) {
            console.error('Error getting suggestions:', error);
        }
    }

    displaySuggestions(suggestions) {
        if (suggestions.length === 0) {
            this.suggestionsDropdown.style.display = 'none';
            return;
        }

        this.suggestionsDropdown.innerHTML = suggestions.map(suggestion => `
            <div class="suggestion-item" onclick="app.selectSuggestion('${suggestion.replace(/'/g, "\\'")}')">
                <i class="fas fa-search suggestion-icon"></i>
                <span>${suggestion}</span>
            </div>
        `).join('');

        this.suggestionsDropdown.style.display = 'block';
    }

    selectSuggestion(suggestion) {
        this.searchInput.value = suggestion;
        this.currentQuery = suggestion;
        this.suggestionsDropdown.style.display = 'none';
        this.performSearch();
    }

    async performSearch(page = 1, searchType = 'all') {
        console.log('performSearch called with:', { page, searchType, currentQuery: this.currentQuery });
        this.currentPage = page;
        this.showLoading(true);

        const startTime = Date.now();

        try {
            // Build query parameters
            const params = new URLSearchParams({
                page: page,
                per_page: 24,
                type: searchType
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
            console.log('Search response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Search response data:', data);

            const searchTime = Date.now() - startTime;
            this.lastSearchTime = searchTime;

            // Update UI
            this.displayUnifiedResults(data);
            this.updateSearchStats(data, searchTime);

            // Search categories if query exists
            if (this.currentQuery) {
                await this.searchCategories(this.currentQuery);
            } else {
                this.categoryResults.style.display = 'none';
            }

        } catch (error) {
            console.error('Search error:', error);
            this.showError('Σφάλμα κατά την αναζήτηση. Παρακαλώ δοκιμάστε ξανά.');
        } finally {
            this.showLoading(false);
        }
    }

    async searchCategories(query) {
        try {
            const response = await fetch(`/categories/search?q=${encodeURIComponent(query)}&limit=5`);
            const categories = await response.json();

            if (categories.length > 0) {
                this.displayCategoryResults(categories);
            } else {
                this.categoryResults.style.display = 'none';
            }
        } catch (error) {
            console.error('Category search error:', error);
            this.categoryResults.style.display = 'none';
        }
    }

    displayCategoryResults(categories) {
        this.categoryList.innerHTML = categories.map(category => {
            const categoryName = category.name || category.key || category;
            const categoryCount = category.total_products || category.unique_products || category.count || 0;
            const safeName = String(categoryName).replace(/'/g, "\\'");
            return `
                <div class="category-item" onclick="app.selectCategory('${safeName}')">
                    <div class="category-name">${categoryName}</div>
                    <div class="category-count">${categoryCount} products</div>
                </div>
            `;
        }).join('');

        this.categoryResults.style.display = 'block';
    }

    selectCategory(categoryName) {
        this.currentFilters.category = categoryName;
        this.updateFilters();
        this.categoryResults.style.display = 'none';
    }

    displayResults(data) {
        console.log(data)
        
        const { products, total, page, per_page, total_pages } = data;
        
        // Update results count
        this.resultsCount.textContent = `${total.toLocaleString()} results`;
        this.resultsMeta.textContent = `Page ${page} of ${total_pages}`;

        if (products.length === 0) {
            this.showNoResults();
            return;
        }

        // Display products with Bootstrap row structure
        this.productGrid.innerHTML = `
            <div class="row">
                ${products.map(product => this.createProductCard(product)).join('')}
            </div>
        `;

        // Update pagination
        this.updatePagination(page, total_pages);

        // Update facets
        if (data.facets) {
            this.updateFacets(data.facets);
        }

        // Show results
        this.noResults.style.display = 'none';
        this.productGrid.style.display = 'block';
    }

    createProductCard(product) {
        // Handle different price formats - check for aggregated vs regular products
        let price = 'Price not available';
        let originalPrice = '';
        let discount = '';

        if (product.best_available_price) {
            // Aggregated product
            price = `€${product.best_available_price.toFixed(2)}`;
            if (product.min_price !== product.max_price) {
                price += ` - €${product.max_price.toFixed(2)}`;
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

            // Original price and discount for regular products
            if (product.original_price && product.original_price > parseFloat(product.price)) {
                originalPrice = `<del class="text-muted">€${product.original_price.toFixed(2)}</del>`;
                discount = `<span class="badge bg-warning text-dark ms-2">-${Math.round(((product.original_price - parseFloat(product.price)) / product.original_price) * 100)}%</span>`;
            }
        }

        const availability = product.availability ? 
            '<span class="badge bg-success">Available</span>' : 
            '<span class="badge bg-danger">Out of Stock</span>';

        const stockInfo = product.stock_quantity ? 
            `<small class="text-muted">Stock: ${product.stock_quantity}</small>` : 
            '<small class="text-muted">Stock: N/A</small>';

        // Handle aggregated vs regular product shop count
        const shopInfo = product.shop_count ? 
            `<small class="text-muted">${product.shop_count} shops</small>` :
            (product.shop ? `<small class="text-muted">${product.shop.name || product.shop}</small>` : '');

        const imageUrl = product.image_url || 'https://via.placeholder.com/200x150?text=No+Image';
        const brandName = product.brand ? (product.brand.name || product.brand) : '';

        return `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100 product-card" onclick="app.showProductDetails(${product.id})">
                    <img src="${imageUrl}" class="card-img-top product-image" alt="${product.title}">
                    <div class="card-body d-flex flex-column">
                        <h6 class="card-title">${product.title}</h6>
                        <p class="card-text text-muted small">${product.description ? product.description.substring(0, 100) + '...' : ''}</p>
                        <div class="mt-auto">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <div class="price">
                                    <strong class="text-primary">${price}</strong>
                                    ${originalPrice}
                                    ${discount}
                                </div>
                                ${availability}
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                ${stockInfo}
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                ${shopInfo}
                                <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); app.showProductDetails(${product.id})">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    updatePagination(currentPage, totalPages) {
        if (totalPages <= 1) {
            this.paginationContainer.innerHTML = '';
            return;
        }

        const paginationItems = this.generatePaginationItems(currentPage, totalPages);
        
        this.paginationContainer.innerHTML = `
            <nav aria-label="Search results pagination">
                <ul class="pagination justify-content-center">
                    ${paginationItems}
                </ul>
            </nav>
        `;
    }

    generatePaginationItems(currentPage, totalPages) {
        let items = '';
        
        // Previous button
        if (currentPage > 1) {
            items += `<li class="page-item"><a class="page-link" href="#" onclick="app.performSearch(${currentPage - 1})">‹</a></li>`;
        }
        
        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        if (startPage > 1) {
            items += `<li class="page-item"><a class="page-link" href="#" onclick="app.performSearch(1)">1</a></li>`;
            if (startPage > 2) {
                items += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            if (i === currentPage) {
                items += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                items += `<li class="page-item"><a class="page-link" href="#" onclick="app.performSearch(${i})">${i}</a></li>`;
            }
        }
        
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                items += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            items += `<li class="page-item"><a class="page-link" href="#" onclick="app.performSearch(${totalPages})">${totalPages}</a></li>`;
        }
        
        // Next button
        if (currentPage < totalPages) {
            items += `<li class="page-item"><a class="page-link" href="#" onclick="app.performSearch(${currentPage + 1})">›</a></li>`;
        }
        
        return items;
    }

    updateSearchStats(data, searchTime) {
        if(typeof(data) === 'undefined') {
            this.resultsCount.innerHTML = '0 Results';
            this.resultsMeta.style.display = 'none'
        } else {
            const total = data.total || (data.products && data.products.total) || 0;
            const stats = `Found <span class="search-speed">${total.toLocaleString()}</span> results in <span class="search-speed">${searchTime}ms</span>`;
            this.searchStats.innerHTML = stats;
            this.searchStats.style.display = 'block';
            this.resultsMeta.style.display = 'block'
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
        // Store complete facets data
        this.facetsData = facets;

        // Update brand filters with search and pagination
        if (facets.brands && facets.brands.length > 0) {
            this.updateBrandFilters(facets.brands);
        }

        // Update category filters with search and pagination
        if (facets.categories && facets.categories.length > 0) {
            this.updateCategoryFilters(facets.categories);
        }

        // Update shop filters with search and multi-select
        if (facets.shops && facets.shops.length > 0) {
            this.updateShopFilters(facets.shops);
        }

        // Update price range slider
        if (facets.price_stats && facets.price_stats.min !== undefined) {
            const minPrice = Math.floor(facets.price_stats.min);
            const maxPrice = Math.ceil(facets.price_stats.max);

            this.priceRangeSlider.noUiSlider.updateOptions({
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

    updateBrandFilters(brands) {
        const visibleBrands = brands
        // .slice(0, this.brandFilterPage * this.itemsPerFilterPage);
        const hasMore = brands.length > this.brandFilterPage * this.itemsPerFilterPage;
        
        this.brandFilters.innerHTML = `
            <div class="filter-search">
                <input type="text" id="brandSearch" placeholder="Search brands..." 
                       onkeyup="app.filterBrands(this.value)">
            </div>
            <div class="filter-options" id="brandOptions" style="height: 30vh; overflow-y: scroll;">
                ${visibleBrands.map(brand => {
                    const brandKey = brand.key || brand.name || brand;
                    const brandCount = brand.doc_count || brand.count || 0;
                    const safeKey = String(brandKey).replace(/'/g, "\\'");
                    const isSelected = this.currentFilters.brands && this.currentFilters.brands.includes(brandKey);
                    return `
                        <div class="filter-option" data-brand="${brandKey.toLowerCase()}">
                            <input type="checkbox" id="brand-${brandKey}" value="${brandKey}" 
                                   ${isSelected ? 'checked' : ''}
                                   onchange="app.handleBrandFilter('${safeKey}', this.checked)">
                            <label for="brand-${brandKey}">${brandKey}</label>
                            <span class="filter-count">${brandCount}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    updateCategoryFilters(categories) {
        const visibleCategories = categories
        // .slice(0, this.categoryFilterPage * this.itemsPerFilterPage);
        const hasMore = categories.length > this.categoryFilterPage * this.itemsPerFilterPage;
        
        this.categoryFilters.innerHTML = `
            <div class="filter-search">
                <input type="text" id="categorySearch" placeholder="Search categories..." 
                       onkeyup="app.filterCategories(this.value)">
            </div>
            <div class="filter-options" id="categoryOptions" style="height: 30vh; overflow-y: scroll;">
                ${visibleCategories.map(category => {
                    const categoryKey = category.key || category.name || category;
                    const categoryCount = category.doc_count || category.count || 0;
                    const safeKey = String(categoryKey).replace(/'/g, "\\'");
                    const isSelected = this.currentFilters.categories && this.currentFilters.categories.includes(categoryKey);
                    return `
                        <div class="filter-option" data-category="${categoryKey.toLowerCase()}">
                            <input type="checkbox" id="category-${categoryKey}" value="${categoryKey}"
                                ${isSelected ? 'checked' : ''}
                                onchange="app.handleCategoryFilter('${safeKey}', this.checked)">
                            <label for="category-${categoryKey}">${categoryKey}</label>
                            <span class="filter-count">${categoryCount}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    updateShopFilters(shops) {
        // Add search box for shops
        const shopFilters = document.getElementById('shopFilters');
        shopFilters.innerHTML = `
            <div class="filter-search">
                <input type="text" id="shopSearch" placeholder="Search shops..." onkeyup="app.filterShops(this.value)">
            </div>
            <div class="filter-options" id="shopOptions" style="height: 30vh; overflow-y: scroll;">
                ${shops.map(shop => {
                    const shopKey = shop.key || shop.name || shop;
                    const shopCount = shop.doc_count || shop.count || 0;
                    const safeKey = String(shopKey).replace(/'/g, "\\'");
                    const isSelected = this.currentFilters.shops && this.currentFilters.shops.includes(shopKey);
                    return `
                        <div class="filter-option" data-shop="${shopKey.toLowerCase()}">
                            <input type="checkbox" id="shop-${shopKey}" value="${shopKey}" 
                                   ${isSelected ? 'checked' : ''}
                                   onchange="app.handleShopFilter('${safeKey}', this.checked)">
                            <label for="shop-${shopKey}">${shopKey}</label>
                            <span class="filter-count">
                                ${shopCount}
                            </span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    filterShops(searchTerm) {
        const shopFilters = document.getElementById('shopFilters');
        const shopOptions = shopFilters.querySelectorAll('.filter-option');
        shopOptions.forEach(option => {
            const label = option.querySelector('label');
            const shopName = label.textContent.toLowerCase();
            const searchLower = searchTerm.toLowerCase();
            if (shopName.includes(searchLower)) {
                option.style.display = 'flex';
            } else {
                option.style.display = 'none';
            }
        });
    }

    handleShopFilter(shop, checked) {
        if (!this.currentFilters.shops) {
            this.currentFilters.shops = [];
        }
        if (checked) {
            if (!this.currentFilters.shops.includes(shop)) {
                this.currentFilters.shops.push(shop);
            }
        } else {
            this.currentFilters.shops = this.currentFilters.shops.filter(s => s !== shop);
            if (this.currentFilters.shops.length === 0) {
                delete this.currentFilters.shops;
            }
        }
        this.updateFilters();
    }

    // showMoreBrands() {
    //     this.brandFilterPage++;
    //     this.updateBrandFilters(this.facetsData.brands);
    // }

    // showMoreCategories() {
    //     this.categoryFilterPage++;
    //     this.updateCategoryFilters(this.facetsData.categories);
    // }

    handleBrandFilter(brand, checked) {
        if (!this.currentFilters.brands) {
            this.currentFilters.brands = [];
        }
        
        if (checked) {
            if (!this.currentFilters.brands.includes(brand)) {
                this.currentFilters.brands.push(brand);
            }
        } else {
            this.currentFilters.brands = this.currentFilters.brands.filter(b => b !== brand);
            if (this.currentFilters.brands.length === 0) {
                delete this.currentFilters.brands;
            }
        }
        this.updateFilters();
    }

    handleCategoryFilter(category, checked) {
        if (!this.currentFilters.categories) {
            this.currentFilters.categories = [];
        }
        
        if (checked) {
            if (!this.currentFilters.categories.includes(category)) {
                this.currentFilters.categories.push(category);
            }
        } else {
            this.currentFilters.categories = this.currentFilters.categories.filter(c => c !== category);
            if (this.currentFilters.categories.length === 0) {
                delete this.currentFilters.categories;
            }
        }
        this.updateFilters();
    }

    filterBrands(searchTerm) {
        const brandOptions = document.getElementById('brandOptions');
        const options = brandOptions.querySelectorAll('.filter-option');
        
        options.forEach(option => {
            const brandName = option.getAttribute('data-brand');
            if (brandName.includes(searchTerm.toLowerCase())) {
                option.style.display = 'block';
            } else {
                option.style.display = 'none';
            }
        });
    }

    filterCategories(searchTerm) {
        const categoryOptions = document.getElementById('categoryOptions');
        const options = categoryOptions.querySelectorAll('.filter-option');
        
        options.forEach(option => {
            const categoryName = option.getAttribute('data-category');
            if (categoryName.includes(searchTerm.toLowerCase())) {
                option.style.display = 'block';
            } else {
                option.style.display = 'none';
            }
        });
    }

    updateFilters() {
        this.updateActiveFilters();
        this.currentPage = 1;
        this.performSearch(this.currentPage);
    }

    updateActiveFilters() {
        const activeFilters = [];

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

        if (this.currentFilters.shops && this.currentFilters.shops.length > 0) {
            this.currentFilters.shops.forEach(shop => {
                activeFilters.push({
                    type: 'shop',
                    value: shop,
                    label: `Shop: ${shop}`
                });
            });
        }

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

        this.activeFilters.innerHTML = activeFilters.map(filter => `
            <div class="filter-tag">
                ${filter.label}
                <span class="remove" onclick="app.removeFilter('${filter.type}', '${filter.value}')">×</span>
            </div>
        `).join('');
    }

    removeFilter(type, value) {
        switch (type) {
            case 'brand':
                if (this.currentFilters.brands) {
                    this.currentFilters.brands = this.currentFilters.brands.filter(b => b !== value);
                    if (this.currentFilters.brands.length === 0) {
                        delete this.currentFilters.brands;
                    }
                }
                break;
            case 'category':
                if (this.currentFilters.categories) {
                    this.currentFilters.categories = this.currentFilters.categories.filter(c => c !== value);
                    if (this.currentFilters.categories.length === 0) {
                        delete this.currentFilters.categories;
                    }
                }
                break;
            case 'shop':
                if (this.currentFilters.shops) {
                    this.currentFilters.shops = this.currentFilters.shops.filter(s => s !== value);
                    if (this.currentFilters.shops.length === 0) {
                        delete this.currentFilters.shops;
                    }
                }
                break;
            case 'availability':
                delete this.currentFilters.availability;
                break;
            case 'price':
                delete this.currentFilters.min_price;
                delete this.currentFilters.max_price;
                break;
        }

        this.updateFilters();
    }

    clearAllFilters() {
        this.currentFilters = {};

        // Reset pagination
        this.brandFilterPage = 1;
        this.categoryFilterPage = 1;

        // Reset form elements
        document.querySelectorAll('.filter-option input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Clear search inputs
        const brandSearch = document.getElementById('brandSearch');
        const categorySearch = document.getElementById('categorySearch');
        if (brandSearch) brandSearch.value = '';
        if (categorySearch) categorySearch.value = '';

        this.minPriceInput.value = '';
        this.maxPriceInput.value = '';

        // Reset price slider
        if (this.priceRangeSlider && this.facetsData.price_stats) {
            this.priceRangeSlider.noUiSlider.set([
                this.facetsData.price_stats.min,
                this.facetsData.price_stats.max
            ]);
        }

        this.updateFilters();
    }

    async showProductDetails(productId) {
        try {
            console.log('Show product details for:', productId);

            // Show modal with loading state
            const modal = new bootstrap.Modal(document.getElementById('productModal'));
            const modalBody = document.getElementById('productModalBody');

            modalBody.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading product details...</p>
                </div>
            `;

            modal.show();

            // Try to get product details from API
            let product = null;
            try {
                const response = await fetch(`/product/${productId}`);
                if (response.ok) {
                    product = await response.json();
                }
            } catch (error) {
                console.log('API endpoint not available, using search data');
            }

            // If API fails, find product in current search results
            if (!product) {
                const productCards = document.querySelectorAll('.product-card');
                let foundProduct = null;

                // Search through current results to find matching product
                const allProducts = Array.from(productCards).map(card => {
                    const title = card.querySelector('.product-title')?.textContent || '';
                    const price = card.querySelector('.product-price')?.textContent || '';
                    const availability = card.querySelector('.product-availability')?.textContent || '';
                    const shop = card.querySelector('.product-shop')?.textContent || '';
                    const image = card.querySelector('.product-image img')?.src || '';

                    return {
                        id: productId,
                        title,
                        price,
                        availability: availability.includes('Available'),
                        shop: shop,
                        image_url: image,
                        description: 'Product details from current search results'
                    };
                });

                product = allProducts[0]; // Use first product as fallback
            }

            // Display product details
            if (product) {
                this.displayProductModal(product);
            } else {
                modalBody.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Product details not available
                    </div>
                `;
            }

        } catch (error) {
            console.error('Error showing product details:', error);
            document.getElementById('productModalBody').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error loading product details: ${error.message}
                </div>
            `;
        }
    }

    displayProductModal(product) {
        const modalBody = document.getElementById('productModalBody');
        const modalTitle = document.getElementById('productModalLabel');

        modalTitle.textContent = product.title || 'Product Details';

        const imageUrl = product.image_url && product.image_url !== 'https://via.placeholder.com/200x150?text=No+Image' 
            ? product.image_url 
            : null;

        const price = product.price ? 
            (typeof product.price === 'string' ? product.price : `€${product.price.toFixed(2)}`) 
            : 'Price not available';

        const originalPrice = product.original_price && product.original_price > parseFloat(product.price) ? 
            `<del class="text-muted ms-2">€${product.original_price.toFixed(2)}</del>` : '';

        const discount = product.original_price && product.original_price > parseFloat(product.price) ?
            `<span class="badge bg-warning text-dark ms-2">-${Math.round(((product.original_price - parseFloat(product.price)) / product.original_price) * 100)}%</span>` : '';

        const availability = product.availability || product.availability === true ? 
            '<span class="badge bg-success">Available</span>' : 
            '<span class="badge bg-danger">Out of Stock</span>';

        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-5">
                    ${imageUrl ? 
                        `<img src="${imageUrl}" class="img-fluid rounded" alt="${product.title}" style="width: 100%; max-height: 300px; object-fit: contain;">` :
                        `<div class="bg-light rounded d-flex align-items-center justify-content-center" style="height: 300px;">
                            <i class="fas fa-image fa-3x text-muted"></i>
                        </div>`
                    }
                </div>
                <div class="col-md-7">
                    <h5 class="mb-3">${product.title}</h5>

                    ${product.description ? `<p class="text-muted mb-3">${product.description}</p>` : ''}

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

                    ${product.stock_quantity ? `
                        <div class="mb-3">
                            <strong>Stock:</strong> ${product.stock_quantity} units
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

    showMobileFilters() {
        this.filterSidebar.classList.add('show');
        this.filterBackdrop.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    hideMobileFilters() {
        this.filterSidebar.classList.remove('show');
        this.filterBackdrop.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    showLoading(show) {
        if (show) {
            this.loadingSpinner.style.display = 'block';
            this.productGrid.style.display = 'none';
            this.noResults.style.display = 'none';
        } else {
            this.loadingSpinner.style.display = 'none';
        }
    }

    showNoResults() {
        this.productGrid.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No products found matching your criteria.
            </div>
        `;
        this.noResults.style.display = 'none';
        this.productGrid.style.display = 'block';
    }

    showError(message) {
        console.error(message);
        this.showLoading(false);
        this.resultsCount.textContent = 'Search error';
        this.resultsMeta.textContent = message;
        this.showNoResults();
    }

    displayUnifiedResults(data) {
        if (data.type === 'unified') {
            
            // Display only products - no categories in product list
            const productsData = data.products || data;
            if (productsData && ((productsData.products && productsData.products.length > 0) || (productsData.length > 0 && !productsData.categories))) {
                const products = productsData.products || productsData;
                
                // Update results count
                const total = productsData.total || products.length;
                this.resultsCount.textContent = `${total.toLocaleString()} results`;
                
                if (productsData.page && productsData.total_pages) {
                    this.resultsMeta.textContent = `Page ${productsData.page} of ${productsData.total_pages}`;
                    this.updatePagination(productsData.page, productsData.total_pages);
                }

                // Display products only
                this.productGrid.innerHTML = `
                    <div class="row">
                        ${products.map(product => {
                            if (product.title) { // Only show actual products, not categories
                                return this.createProductCard(product);
                            }
                            return '';
                        }).join('')}
                    </div>
                `;

                // Update facets if available
                if (productsData.facets) {
                    this.updateFacets(productsData.facets);
                }

                this.noResults.style.display = 'none';
                this.productGrid.style.display = 'grid';
                this.resultsContainer.style.display = 'block';
            } else {
                this.showNoResults();
                // data.total = 0;
                // this.displayResults(data);
                this.updateSearchStats()
            }
        } else {
            // Handle single type results (products only)
            this.displayResults(data);
        }
    }

    createAggregatedProductCard(product) {
        const availabilityText = product.availability ? 
            `Available in ${product.available_shops}/${product.shop_count} shops` :
            `Available in 3-7 days`;

        const priceText = product.best_available_price ? 
            `Best: €${product.best_available_price.toFixed(2)}` :
            `From: €${product.min_price?.toFixed(2) || 'N/A'}`;

        return `
            <div class="product-card aggregated" onclick="app.showProductDetails(${product.product_ids[0]})">
                <img src="${product.image_url || '/static/placeholder.jpg'}" alt="${product.title}" loading="lazy">
                <div class="product-info">
                    <h3 class="product-title">${product.title}</h3>
                    <p class="product-brand">${product.brand?.name || ''}</p>
                    <div class="price-info">
                        <span class="price">${priceText}</span>
                        ${product.min_price !== product.max_price ? 
                            `<span class="price-range">Range: €${product.min_price?.toFixed(2)} - €${product.max_price?.toFixed(2)}</span>` : ''
                        }
                    </div>
                    <div class="availability-info">
                        <span class="availability ${product.availability ? 'available' : 'limited'}">${availabilityText}</span>
                        <span class="shop-count">${product.shop_count} shops</span>
                    </div>
                    <div class="delivery-info">${product.availability_info.estimated_delivery}</div>
                </div>
            </div>
        `;
    }

    searchInCategory(categoryName) {
        this.currentFilters.category = categoryName;
        this.updateFilters();
        this.performSearch(1, 'products');
    }
}

let appInitialized = false;
function initializeApp() {
    console.log('initializeApp called, appInitialized:', appInitialized);
    if (!appInitialized) {
        console.log('Creating new ModernSearchApp instance...');
        window.app = new ModernSearchApp();
        appInitialized = true;
    } else {
        console.log('App already initialized, re-initializing elements...');
        // Re-initialize elements for the new DOM
        window.app.initializeElements();
        window.app.setupEventListeners();
        window.app.setupPriceRangeSlider();
    }
    
    // Set up event listeners for the header search bar after a short delay
    setTimeout(() => {
        console.log('Setting up header search event listeners...');
        const headerSearchInput = document.getElementById('mainSearch');
        const headerSearchBtn = document.getElementById('searchBtn');
        
        console.log('Header elements found:', {
            searchInput: !!headerSearchInput,
            searchBtn: !!headerSearchBtn
        });
        
        if (headerSearchInput && window.app) {
            // Set up event listeners for header search
            headerSearchInput.addEventListener('input', (e) => {
                console.log('Header search input:', e.target.value);
                window.app.handleSearchInput(e.target.value);
            });
            
            headerSearchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    console.log('Header search Enter pressed');
                    window.app.currentPage = 1;
                    window.app.performSearch(window.app.currentPage);
                }
            });
        }
        
        if (headerSearchBtn && window.app) {
            headerSearchBtn.addEventListener('click', () => {
                console.log('Header search button clicked');
                window.app.currentPage = 1;
                window.app.performSearch(window.app.currentPage);
            });
        }
    }, 300);
}
document.addEventListener('DOMContentLoaded', function () {
    const landingContainer = document.getElementById('landingContainer');
    const mainContent = document.getElementById('mainContent');
    const searchInput = document.getElementById('mainSearch');
    const burgerMenu = document.getElementById('burgerMenu');
    const burgerDropdown = document.getElementById('burgerDropdown');
    const logo = document.getElementById('logo');

    // Burger menu show/hide (only on landing page)
    let burgerOpen = false;
    function showBurgerDropdown() {
        burgerDropdown.classList.add('show');
        burgerOpen = true;
    }
    function hideBurgerDropdown() {
        burgerDropdown.classList.remove('show');
        burgerOpen = false;
    }
    function landingBurgerHandler(e) {
        if (landingContainer.style.display === 'none') return; // Disable after landing
        e.stopPropagation();
        burgerOpen ? hideBurgerDropdown() : showBurgerDropdown();
    }
    function landingDocHandler(e) {
        if (landingContainer.style.display === 'none') return;
        if (!burgerMenu.contains(e.target) && !burgerDropdown.contains(e.target)) {
            hideBurgerDropdown();
        }
    }
    burgerMenu.addEventListener('click', landingBurgerHandler);
    document.addEventListener('click', landingDocHandler);

    // Logo click opens admin page
    logo.addEventListener('click', function () {
        window.open('/admin', '_blank');
    });

    // Animate search bar to top and show main content on input
    let searchActivated = false;
    searchInput.addEventListener('input', function (e) {
        if (!searchActivated && searchInput.value.trim() !== '') {
            landingContainer.classList.add('search-active');
            mainContent.style.display = 'block';
            searchActivated = true;
        } else if (searchActivated && searchInput.value.trim() === '') {
            landingContainer.classList.remove('search-active');
            mainContent.style.display = 'none';
            searchActivated = false;
        }
    });

    // On Enter, inject main content HTML and initialize app
    searchInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && searchInput.value.trim() !== '') {
            const searchQuery = searchInput.value.trim();
            landingContainer.style.display = 'none';
            mainContent.innerHTML = `
            <!-- Header with logo, search bar, and burger -->
            <div class="search-header" style="background: white; padding: 15px 20px; border-bottom: 1px solid #eee; position: sticky; top: 0; z-index: 1000;">
                <div class="container-fluid">
                    <div class="row align-items-center">
                        <div class="col-md-4">
                            <div class="logo" style="font-size: 1.8rem; font-weight: 700; color: #1974d0; cursor: pointer;" onclick="window.open('/admin', '_blank')">Market.gr</div>
                        </div>
                        <div class="col-md-5">
                            <div class="search-bar-wrapper" style="display: flex; align-items: center; background: #f8f9fa; border-radius: 1rem; padding: 0.5rem 1rem; border: 1px solid #ddd;">
                                <input id="mainSearch" class="main-search" type="text" placeholder="Search..." autocomplete="on" value="${searchQuery}" style="border: none; outline: none; font-size: 1rem; flex: 1; background: transparent; padding: 0.5rem 0;">
                                <button id="searchBtn" class="search-btn" style="background: none; border: none; color: #1974d0; font-size: 1.1rem; margin-left: 0.5rem; cursor: pointer;"><i class="fas fa-search"></i></button>
                            </div>
                        </div>
                        <div class="col-md-3 text-end">
                            <div style="position: relative;">
                                <div id="burgerMenu" class="burger-menu" style="display: inline-block; position: relative; top: 0; right: 0; width: 40px; height: 40px; display: flex; flex-direction: column; justify-content: center; align-items: center; cursor: pointer; margin-left: auto;">
                                    <span style="display: block; width: 28px; height: 4px; background: #1974d0; margin: 3px 0; border-radius: 2px;"></span>
                                    <span style="display: block; width: 28px; height: 4px; background: #1974d0; margin: 3px 0; border-radius: 2px;"></span>
                                    <span style="display: block; width: 28px; height: 4px; background: #1974d0; margin: 3px 0; border-radius: 2px;"></span>
                                </div>
                                <div id="burgerDropdown" class="burger-dropdown" style="display: none; position: absolute; top: 48px; right: 0; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.12); min-width: 160px; padding: 0.5rem 0; z-index: 100;">
                                    <ul style="list-style: none; margin: 0; padding: 0;">
                                        <li style="padding: 0.75rem 1.5rem; color: #1974d0; font-size: 1rem; cursor: pointer; display: flex; align-items: center; gap: 0.75rem; transition: background 0.2s;"><i class="fas fa-user"></i> Login</li>
                                        <li style="padding: 0.75rem 1.5rem; color: #1974d0; font-size: 1rem; cursor: pointer; display: flex; align-items: center; gap: 0.75rem; transition: background 0.2s;"><i class="fas fa-clock"></i> History</li>
                                        <li style="padding: 0.75rem 1.5rem; color: #1974d0; font-size: 1rem; cursor: pointer; display: flex; align-items: center; gap: 0.75rem; transition: background 0.2s;"><i class="fas fa-file-alt"></i> Terms</li>
                                        <li style="padding: 0.75rem 1.5rem; color: #1974d0; font-size: 1rem; cursor: pointer; display: flex; align-items: center; gap: 0.75rem; transition: background 0.2s;"><i class="fas fa-comments"></i> Chat</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Main content -->
            <div class="container-fluid" style="padding-top: 20px;">
                <div class="row">
                    <div class="col-lg-3 col-md-4 mb-4">
                        <div class="filter-sidebar" id="filterSidebar">
                            <div class="active-filters" id="activeFilters"></div>
                            <div class="filter-section">
                                <div class="filter-title"><i class="fas fa-euro-sign me-2"></i>Price</div>
                                <div class="price-range-container">
                                    <div id="priceRangeSlider"></div>
                                    <div class="price-inputs">
                                        <input type="number" class="price-input" id="minPrice" placeholder="Min">
                                        <input type="number" class="price-input" id="maxPrice" placeholder="Max">
                                    </div>
                                </div>
                            </div>
                            <div class="filter-section">
                                <div class="filter-title"><i class="fas fa-check-circle me-2"></i>Availability</div>
                                <div class="filter-option">
                                    <input type="checkbox" id="availableOnly" value="true">
                                    <label for="availableOnly">Available only</label>
                                </div>
                                <div class="filter-option">
                                    <input type="checkbox" id="inStock" value="true">
                                    <label for="inStock">In stock</label>
                                </div>
                            </div>
                            <div class="filter-section">
                                <div class="filter-title"><i class="fas fa-tag me-2"></i>Brand</div>
                                <div id="brandFilters"></div>
                            </div>
                            <div class="filter-section">
                                <div class="filter-title"><i class="fas fa-layer-group me-2"></i>Category</div>
                                <div id="categoryFilters"></div>
                            </div>
                            <div class="filter-section">
                                <div class="filter-title"><i class="fas fa-store me-2"></i>Shop</div>
                                <div id="shopFilters" style="height: 30vh; overflow-y: scroll;"></div>
                            </div>
                            <button class="clear-filters" id="clearFilters"><i class="fas fa-undo me-2"></i>Clear filters</button>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8">
                        <div class="category-results" id="categoryResults" style="display: none;">
                            <div class="category-header"><i class="fas fa-layer-group me-2"></i>Categories</div>
                            <div class="category-list" id="categoryList"></div>
                        </div>
                        <div class="results-container" id="resultsContainer">
                            <div class="search-stats" id="searchStats" style="display: none;"></div>
                            <div class="results-header" id="resultsHeader">
                                <div class="results-count" id="resultsCount">Searching products...</div>
                                <span>&nbsp;&nbsp;</span>
                                <div class="results-meta" id="resultsMeta"></div>
                                <div class="sort-controls" style="margin-left: 20px;">
                                    <select class="sort-select" id="sortSelect">
                                        <option value="relevance">Relevance</option>
                                        <option value="price_asc">Price (Low to High)</option>
                                        <option value="price_desc">Price (High to Low)</option>
                                        <option value="availability">Availability</option>
                                        <option value="newest">Newest First</option>
                                    </select>
                                </div>
                            </div>
                            <div class="loading-spinner" id="loadingSpinner">
                                <div class="spinner-border" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <div class="mt-3">Searching products...</div>
                            </div>
                            <div class="no-results" id="noResults" style="display: none;">
                                <i class="fas fa-search"></i>
                                <h5>No results found</h5>
                                <p>Try different search terms or clear the filters</p>
                            </div>
                            <div class="product-grid" id="productGrid"></div>
                            <div class="pagination-container" id="paginationContainer"></div>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Hidden elements for JavaScript -->
            <select id="languageSelect" style="display: none;">
                <option value="el">Ελληνικά</option>
                <option value="en">English</option>
            </select>
            <button id="voiceBtn" style="display: none;"><i class="fas fa-microphone"></i></button>
            <button id="imageBtn" style="display: none;"><i class="fas fa-camera"></i></button>
            <button id="micBtn" style="display: none;"><i class="fas fa-microphone"></i></button>
            <input type="file" id="imageInput" style="display: none;" accept="image/*">
            <button class="mobile-filter-btn" id="mobileFilterBtn"><i class="fas fa-filter"></i></button>
            <div class="filter-backdrop" id="filterBackdrop">
                <div class="mobile-filter-sidebar">
                    <div class="mobile-filter-header">
                        <h5>Filters</h5>
                        <button class="close-mobile-filters" id="closeMobileFilters"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="mobile-filter-content">
                        <div class="filter-section">
                            <div class="filter-title"><i class="fas fa-euro-sign me-2"></i>Price</div>
                            <div class="price-inputs">
                                <input type="number" class="price-input" placeholder="Min">
                                <input type="number" class="price-input" placeholder="Max">
                            </div>
                        </div>
                        <div class="filter-section">
                            <div class="filter-title"><i class="fas fa-check-circle me-2"></i>Availability</div>
                            <div class="filter-option">
                                <input type="checkbox" value="true">
                                <label>Available only</label>
                            </div>
                            <div class="filter-option">
                                <input type="checkbox" value="true">
                                <label>In stock</label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal fade" id="productModal" tabindex="-1" aria-labelledby="productModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="productModalLabel">Product Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="productModalBody">
                            <div class="text-center">
                                <div class="spinner-border" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
            `;
            mainContent.style.display = 'block';
            mainContent.style.visibility = 'visible';
            mainContent.style.opacity = '1';
            // Remove burger dropdown and its event listeners
            burgerDropdown.style.display = 'none';
            burgerMenu.removeEventListener('click', landingBurgerHandler);
            document.removeEventListener('click', landingDocHandler);
            burgerMenu.onclick = function(){};
            // Initialize the main app
            initializeApp();
            
            // Perform the search with the query
            setTimeout(() => {
                console.log('Performing initial search with query:', searchQuery);
                if (window.app) {
                    window.app.currentQuery = searchQuery;
                    window.app.performSearch(1);
                } else {
                    console.error('App not initialized');
                }
            }, 500);
            
            // Set up burger dropdown functionality for search results page
            setTimeout(() => {
                const searchBurgerMenu = document.getElementById('burgerMenu');
                const searchBurgerDropdown = document.getElementById('burgerDropdown');
                
                console.log('Setting up burger dropdown:', {
                    menu: !!searchBurgerMenu,
                    dropdown: !!searchBurgerDropdown
                });
                
                if (searchBurgerMenu && searchBurgerDropdown) {
                    let burgerOpen = false;
                    
                    function showBurgerDropdown() {
                        searchBurgerDropdown.style.display = 'block';
                        burgerOpen = true;
                        console.log('Burger dropdown shown');
                    }
                    
                    function hideBurgerDropdown() {
                        searchBurgerDropdown.style.display = 'none';
                        burgerOpen = false;
                        console.log('Burger dropdown hidden');
                    }
                    
                    // Remove any existing listeners
                    searchBurgerMenu.removeEventListener('click', searchBurgerMenu.burgerClickHandler);
                    document.removeEventListener('click', document.burgerDocHandler);
                    
                    // Create new handlers
                    searchBurgerMenu.burgerClickHandler = function (e) {
                        e.stopPropagation();
                        console.log('Burger menu clicked');
                        burgerOpen ? hideBurgerDropdown() : showBurgerDropdown();
                    };
                    
                    document.burgerDocHandler = function (e) {
                        if (!searchBurgerMenu.contains(e.target) && !searchBurgerDropdown.contains(e.target)) {
                            hideBurgerDropdown();
                        }
                    };
                    
                    searchBurgerMenu.addEventListener('click', searchBurgerMenu.burgerClickHandler);
                    document.addEventListener('click', document.burgerDocHandler);
                }
            }, 300);
        }
    });
});

// Prevent default form submission
document.addEventListener('click', (e) => {
    if (e.target.matches('a[href="#"]')) {
        e.preventDefault();
    }
});
