
-- Database structure for E-commerce Search API
-- Generated from SQLAlchemy models

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Create tables

-- Shops table
CREATE TABLE shops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    xml_url VARCHAR(500) NOT NULL,
    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    total_products INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Brands table
CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    normalized_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    path VARCHAR(1000),
    level INTEGER DEFAULT 0,
    parent_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    
    -- Basic product info
    title VARCHAR(1000) NOT NULL,
    description TEXT,
    ean VARCHAR(50),
    mpn VARCHAR(100),
    sku VARCHAR(100),
    
    -- Pricing
    price DECIMAL(10,2),
    original_price DECIMAL(10,2),
    discount_percentage DECIMAL(5,2),
    
    -- Availability
    availability BOOLEAN DEFAULT FALSE,
    stock_quantity INTEGER,
    
    -- Images and media
    image_url VARCHAR(1000),
    additional_images JSONB,
    
    -- SEO and URLs
    product_url VARCHAR(1000),
    deeplink VARCHAR(1000),
    
    -- Specifications and features
    specifications JSONB,
    features JSONB,
    
    -- Search and categorization
    search_text TEXT,
    tags JSONB,
    
    -- Foreign keys
    shop_id INTEGER NOT NULL REFERENCES shops(id),
    brand_id INTEGER REFERENCES brands(id),
    category_id INTEGER REFERENCES categories(id),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product variants table
CREATE TABLE product_variants (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    -- Variant attributes
    color VARCHAR(100),
    size VARCHAR(100),
    material VARCHAR(100),
    style VARCHAR(100),
    
    -- Variant-specific data
    ean VARCHAR(50),
    sku VARCHAR(100),
    price DECIMAL(10,2),
    availability BOOLEAN DEFAULT FALSE,
    stock_quantity INTEGER,
    image_url VARCHAR(1000),
    
    -- Additional variant attributes
    attributes JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance

-- Brands indexes
CREATE INDEX idx_brands_name ON brands(name);
CREATE INDEX idx_brands_normalized ON brands(normalized_name);

-- Categories indexes
CREATE INDEX idx_categories_name ON categories(name);
CREATE INDEX idx_categories_path ON categories(path);
CREATE INDEX idx_categories_normalized ON categories(normalized_name);

-- Products indexes
CREATE INDEX idx_products_ean ON products(ean);
CREATE INDEX idx_products_mpn ON products(mpn);
CREATE INDEX idx_products_title ON products(title);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_availability ON products(availability);
CREATE INDEX idx_products_shop_id ON products(shop_id);
CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_search_text ON products USING gin(to_tsvector('english', search_text));
CREATE INDEX idx_products_specifications ON products USING gin(specifications);

-- Product variants indexes
CREATE INDEX idx_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_variants_ean ON product_variants(ean);
CREATE INDEX idx_variants_color ON product_variants(color);
CREATE INDEX idx_variants_size ON product_variants(size);
CREATE INDEX idx_variants_availability ON product_variants(availability);
CREATE INDEX idx_variants_attributes ON product_variants USING gin(attributes);

-- Full-text search indexes
CREATE INDEX idx_products_title_fts ON products USING gin(to_tsvector('english', title));
CREATE INDEX idx_products_description_fts ON products USING gin(to_tsvector('english', description));

-- Composite indexes for common queries
CREATE INDEX idx_products_availability_price ON products(availability, price);
CREATE INDEX idx_products_brand_category ON products(brand_id, category_id);
CREATE INDEX idx_products_shop_availability ON products(shop_id, availability);

-- Trigram indexes for similarity search (requires pg_trgm extension)
CREATE INDEX idx_products_title_trgm ON products USING gin(title gin_trgm_ops);
CREATE INDEX idx_brands_name_trgm ON brands USING gin(name gin_trgm_ops);
CREATE INDEX idx_categories_name_trgm ON categories USING gin(name gin_trgm_ops);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for automatic timestamp updates
CREATE TRIGGER shops_updated_at
    BEFORE UPDATE ON shops
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER product_variants_updated_at
    BEFORE UPDATE ON product_variants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Sample data insertion (optional)
INSERT INTO shops (name, xml_url) VALUES 
    ('EKOS', 'https://www.ekos.gr/xml/skroutz.xml'),
    ('BEQ', 'https://www.beq.gr/xml/skroutz.xml'),
    ('Zoro', 'https://www.zoro.gr/xml/skroutz.xml'),
    ('1-3.gr', 'https://www.1-3.gr/xml/skroutz.xml');


-- Views for common queries

-- Product summary view
CREATE VIEW product_summary AS
SELECT 
    p.id,
    p.title,
    p.price,
    p.availability,
    s.name as shop_name,
    b.name as brand_name,
    c.name as category_name,
    p.image_url,
    p.created_at
FROM products p
LEFT JOIN shops s ON p.shop_id = s.id
LEFT JOIN brands b ON p.brand_id = b.id
LEFT JOIN categories c ON p.category_id = c.id;

-- Category statistics view
CREATE VIEW category_stats AS
SELECT 
    c.id,
    c.name,
    c.path,
    COUNT(p.id) as product_count,
    AVG(p.price) as avg_price,
    COUNT(CASE WHEN p.availability = true THEN 1 END) as available_products
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
GROUP BY c.id, c.name, c.path;

-- Brand statistics view
CREATE VIEW brand_stats AS
SELECT 
    b.id,
    b.name,
    COUNT(p.id) as product_count,
    AVG(p.price) as avg_price,
    MIN(p.price) as min_price,
    MAX(p.price) as max_price,
    COUNT(CASE WHEN p.availability = true THEN 1 END) as available_products
FROM brands b
LEFT JOIN products p ON b.id = p.brand_id
GROUP BY b.id, b.name;

-- Shop statistics view
CREATE VIEW shop_stats AS
SELECT 
    s.id,
    s.name,
    s.last_sync,
    s.sync_status,
    COUNT(p.id) as product_count,
    COUNT(CASE WHEN p.availability = true THEN 1 END) as available_products,
    AVG(p.price) as avg_price
FROM shops s
LEFT JOIN products p ON s.id = p.shop_id
GROUP BY s.id, s.name, s.last_sync, s.sync_status;

-- Comments for documentation
COMMENT ON TABLE shops IS 'E-commerce shops with XML feeds';
COMMENT ON TABLE brands IS 'Product brands';
COMMENT ON TABLE categories IS 'Product categories with hierarchical structure';
COMMENT ON TABLE products IS 'Main products table with all product information';
COMMENT ON TABLE product_variants IS 'Product variants (colors, sizes, etc.)';

COMMENT ON COLUMN products.search_text IS 'Denormalized search field for full-text search';
COMMENT ON COLUMN products.specifications IS 'JSON field for flexible product specifications';
COMMENT ON COLUMN products.features IS 'JSON field for product features';
COMMENT ON COLUMN categories.path IS 'Full category path for hierarchical navigation';
COMMENT ON COLUMN categories.level IS 'Category hierarchy level (0 = root)';
