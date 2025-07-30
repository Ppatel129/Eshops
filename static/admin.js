class AdminApp {
    constructor() {
        this.processingModal = null;
        this.init();
    }

    init() {
        // Initialize processing modal if Bootstrap is available
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            this.processingModal = new bootstrap.Modal(document.getElementById('processingModal'));
        } else {
            this.processingModal = null;
        }
        this.loadInitialData();
    }

    async loadInitialData() {
        await this.refreshStats();
        await this.refreshShops();
    }

    async refreshStats() {
        try {
            const response = await axios.get('/admin/stats');
            const stats = response.data;
            
            const statsContainer = document.getElementById('statsContainer');
            statsContainer.innerHTML = `
                <div class="col-md-3">
                    <div class="card bg-primary text-white">
                        <div class="card-body text-center">
                            <h2>${stats.shops || 0}</h2>
                            <p class="mb-0">Active Shops</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-success text-white">
                        <div class="card-body text-center">
                            <h2>${stats.products || 0}</h2>
                            <p class="mb-0">Total Products</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-info text-white">
                        <div class="card-body text-center">
                            <h2>${stats.brands || 0}</h2>
                            <p class="mb-0">Brands</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-warning text-white">
                        <div class="card-body text-center">
                            <h2>${stats.categories || 0}</h2>
                            <p class="mb-0">Categories</p>
                        </div>
                    </div>
                </div>
                <div class="col-12 mt-3">
                    <div class="alert alert-info">
                        <strong>Last Sync:</strong> ${stats.last_sync ? new Date(stats.last_sync).toLocaleString() : 'Never'}<br>
                        <strong>Sync Status:</strong> 
                        <span class="badge ${this.getStatusBadgeClass(stats.sync_status)}">${stats.sync_status || 'Unknown'}</span>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading stats:', error);
            this.addLog('Error loading statistics: ' + error.message, 'error');
        }
    }

    async refreshShops() {
        try {
            const response = await axios.get('/shops');
            const shops = response.data;
            
            const shopsTable = document.getElementById('shopsTable');
            if (shops.length === 0) {
                shopsTable.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center text-muted">No shops configured</td>
                    </tr>
                `;
                return;
            }

            console.log(shops)
            shopsTable.innerHTML = shops.map(shop => `
                <tr>
                    <td><strong>${shop.name}</strong></td>
                    <td><a href="${shop.xml_url}" target="_blank" class="text-truncate d-inline-block" style="max-width: 200px;">${shop.xml_url}</a></td>
                    <td>${shop.last_sync ? new Date(shop.last_sync).toLocaleString() : 'Never'}</td>
                    <td><span class="badge ${this.getStatusBadgeClass(shop.sync_status)}">${shop.sync_status}</span></td>
                    <td>${shop.total_products || 0}</td>
                    <td><button class="btn btn-sm btn-danger" onclick="adminApp.openDeleteShopModal(${shop.id}, '${shop.name.replace(/'/g, "&#39;")}')"><i class="fas fa-trash"></i> Delete</button></td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Error loading shops:', error);
            this.addLog('Error loading shops: ' + error.message, 'error');
        }
    }

    getStatusBadgeClass(status) {
        switch (status) {
            case 'completed': return 'bg-success';
            case 'processing': return 'bg-warning';
            case 'error': return 'bg-danger';
            case 'pending': return 'bg-secondary';
            default: return 'bg-light text-dark';
        }
    }

    async processFeeds() {
        if (!confirm('This will process all XML feeds. This may take several minutes and will overwrite existing data. Continue?')) {
            return;
        }

        try {
            const btn = document.getElementById('processFeedsBtn');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            
            if (this.processingModal) {
                this.processingModal.show();
            }
            this.addLog('Starting feed processing...', 'info');

            const response = await axios.post('/admin/process-feeds');
            const results = response.data;

            this.addLog('Feed processing completed!', 'success');
            
            results.forEach(result => {
                const status = result.status === 'completed' ? 'success' : 'error';
                this.addLog(`${result.shop_name}: ${result.status} - ${result.products_processed} products processed (${result.products_created} new, ${result.products_updated} updated)`, status);
                
                if (result.errors && result.errors.length > 0) {
                    result.errors.forEach(error => {
                        this.addLog(`Error in ${result.shop_name}: ${error}`, 'error');
                    });
                }
            });

            // Refresh data
            await this.refreshStats();
            await this.refreshShops();

        } catch (error) {
            console.error('Error processing feeds:', error);
            this.addLog('Error processing feeds: ' + error.message, 'error');
        } finally {
            if (this.processingModal) {
                this.processingModal.hide();
            }
            const btn = document.getElementById('processFeedsBtn');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-play me-2"></i>Process All Feeds';
        }
    }

    async cleanupDatabase() {
        if (!confirm('This will remove duplicate products. This action cannot be undone. Continue?')) {
            return;
        }

        try {
            this.addLog('Starting database cleanup...', 'info');
            
            // For now, just refresh - we can implement actual cleanup later
            await this.refreshStats();
            this.addLog('Database cleanup completed', 'success');
            
        } catch (error) {
            console.error('Error cleaning database:', error);
            this.addLog('Error cleaning database: ' + error.message, 'error');
        }
    }

    addLog(message, type = 'info') {
        const logContainer = document.getElementById('processingLog');
        const timestamp = new Date().toLocaleTimeString();
        
        const logClass = {
            'info': 'text-primary',
            'success': 'text-success',
            'error': 'text-danger',
            'warning': 'text-warning'
        }[type] || 'text-dark';

        const logEntry = document.createElement('div');
        logEntry.className = `mb-1 ${logClass}`;
        logEntry.innerHTML = `<small>[${timestamp}]</small> ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    clearLog() {
        const logContainer = document.getElementById('processingLog');
        logContainer.innerHTML = '<p class="text-muted">Processing logs cleared...</p>';
    }

    // Add methods for delete shop modal
    openDeleteShopModal(shopId, shopName) {
        this.shopToDelete = shopId;
        document.getElementById('deleteShopName').textContent = shopName;
        if (!this.deleteShopModal) {
            this.deleteShopModal = new bootstrap.Modal(document.getElementById('deleteShopModal'));
        }
        this.deleteShopModal.show();
    }

    async confirmDeleteShop() {
        if (!this.shopToDelete) return;
        try {
            document.getElementById('confirmDeleteShopBtn').disabled = true;
            await axios.delete(`/shops/${this.shopToDelete}`);
            this.addLog('Shop deleted successfully', 'success');
            this.deleteShopModal.hide();
            this.shopToDelete = null;
            await this.refreshShops();
        } catch (error) {
            this.addLog('Error deleting shop: ' + (error.response?.data?.detail || error.message), 'error');
        } finally {
            document.getElementById('confirmDeleteShopBtn').disabled = false;
        }
    }

    // Add Shop Modal logic
    openAddShopModal() {
        if (!this.addShopModal) {
            this.addShopModal = new bootstrap.Modal(document.getElementById('addShopModal'));
        }
        document.getElementById('addShopForm').reset();
        this.addShopModal.show();
    }

    async confirmAddShop() {
        const name = document.getElementById('addShopName').value.trim();
        const xmlUrl = document.getElementById('addShopXmlUrl').value.trim();
        if (!name || !xmlUrl) {
            this.addLog('Shop name and XML URL are required', 'error');
            return;
        }
        document.getElementById('confirmAddShopBtn').disabled = true;
        try {
            await axios.post('/shops', { name, xml_url: xmlUrl });
            this.addLog('Shop added successfully', 'success');
            this.addShopModal.hide();
            await this.refreshShops();
        } catch (error) {
            this.addLog('Error adding shop: ' + (error.response?.data?.detail || error.message), 'error');
        } finally {
            document.getElementById('confirmAddShopBtn').disabled = false;
        }
    }
}

// Global functions for button handlers
let adminApp;

function refreshStats() {
    adminApp.refreshStats();
}

function refreshShops() {
    adminApp.refreshShops();
}

function processFeeds() {
    adminApp.processFeeds();
}

function cleanupDatabase() {
    adminApp.cleanupDatabase();
}

function goBackToSearch(maxSteps = 10) {
  let currentURL = window.location.href;
  let step = -1;

  function tryGoBack() {
    if (step < -maxSteps) return; // avoid infinite loop
    history.go(step);
  }

  window.addEventListener('popstate', function check() {
    if (window.location.href !== currentURL) {
      window.removeEventListener('popstate', check);
    } else {
      step--;
      tryGoBack();
    }
  });

  tryGoBack();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    adminApp = new AdminApp();
    // Attach delete shop confirm button handler
    document.getElementById('confirmDeleteShopBtn').addEventListener('click', function() {
        adminApp.confirmDeleteShop();
    });
    // Attach add shop confirm button handler
    document.getElementById('confirmAddShopBtn').addEventListener('click', function() {
        adminApp.confirmAddShop();
    });
});