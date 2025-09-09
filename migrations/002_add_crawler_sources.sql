-- 创建爬取源表
CREATE TABLE IF NOT EXISTS crawler_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    url VARCHAR(500) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    interval INTEGER DEFAULT 60 NOT NULL,
    selector VARCHAR(500) DEFAULT 'article',
    category VARCHAR(100) NOT NULL,
    last_crawled TIMESTAMP,
    article_count INTEGER DEFAULT 0 NOT NULL,
    success_count INTEGER DEFAULT 0 NOT NULL,
    failure_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_enabled_interval ON crawler_sources (enabled, interval);
CREATE INDEX IF NOT EXISTS idx_category ON crawler_sources (category);
CREATE INDEX IF NOT EXISTS idx_last_crawled ON crawler_sources (last_crawled);

-- 向articles表添加source_id字段（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='articles' AND column_name='source_id') THEN
        ALTER TABLE articles ADD COLUMN source_id INTEGER;
        ALTER TABLE articles ADD CONSTRAINT fk_source 
            FOREIGN KEY (source_id) REFERENCES crawler_sources(id) ON DELETE SET NULL;
        CREATE INDEX idx_articles_source_id ON articles(source_id);
    END IF;
END $$;

-- 添加更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_crawler_sources_updated_at ON crawler_sources;
CREATE TRIGGER update_crawler_sources_updated_at 
    BEFORE UPDATE ON crawler_sources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();