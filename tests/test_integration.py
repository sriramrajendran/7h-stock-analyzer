import pytest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestIntegration:
    """Test integration points and project structure"""
    
    def test_config_file_loading(self):
        """Test that configuration files can be loaded"""
        
        # Get the project root directory (tests/ -> project root)
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        # Test portfolio config
        portfolio_config = os.path.join(project_root, 'input', 'config_portfolio.txt')
        if os.path.exists(portfolio_config):
            with open(portfolio_config, 'r') as f:
                content = f.read().strip()
                assert len(content) > 0
        
        # Test watchlist config
        watchlist_config = os.path.join(project_root, 'input', 'config_watchlist.txt')
        if os.path.exists(watchlist_config):
            with open(watchlist_config, 'r') as f:
                content = f.read().strip()
                assert len(content) > 0
    
    def test_requirements_file(self):
        """Test that requirements.txt exists and has content"""
        # Get the project root directory (tests/ -> project root)
        project_root = os.path.dirname(os.path.dirname(__file__))
        requirements_path = os.path.join(project_root, 'requirements.txt')
        assert os.path.exists(requirements_path)
        
        with open(requirements_path, 'r') as f:
            requirements = f.read()
            assert len(requirements) > 0
            assert 'flask' in requirements
            assert 'yfinance' in requirements

    def test_app_py_exists(self):
        """Test that main app file exists"""
        # Get the project root directory (tests/ -> project root)
        project_root = os.path.dirname(os.path.dirname(__file__))
        app_path = os.path.join(project_root, 'app.py')
        assert os.path.exists(app_path)
        
        with open(app_path, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert 'Flask' in content
            assert 'app' in content

    def test_stock_analyzer_py_exists(self):
        """Test that stock analyzer file exists"""
        # Get the project root directory (tests/ -> project root)
        project_root = os.path.dirname(os.path.dirname(__file__))
        analyzer_path = os.path.join(project_root, 'core', 'stock_analyzer.py')
        assert os.path.exists(analyzer_path)
        
        with open(analyzer_path, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert 'StockAnalyzer' in content

    def test_templates_exist(self):
        """Test that HTML templates exist"""
        # Get the project root directory (tests/ -> project root)
        project_root = os.path.dirname(os.path.dirname(__file__))
        base_template = os.path.join(project_root, 'assets', 'base.html')
        index_template = os.path.join(project_root, 'assets', 'index.html')
        
        assert os.path.exists(base_template)
        assert os.path.exists(index_template)
        
        # Check template content
        with open(base_template, 'r') as f:
            base_content = f.read()
            assert '7H Stock Analyzer' in base_content
            assert '<html' in base_content
        
        with open(index_template, 'r') as f:
            index_content = f.read()
            assert 'Portfolio Analysis' in index_content
            assert '<form' in index_content

    def test_static_files_exist(self):
        """Test that static CSS and JS files exist"""
        # Get the project root directory (tests/ -> project root)
        project_root = os.path.dirname(os.path.dirname(__file__))
        css_path = os.path.join(project_root, 'assets', 'css', 'style.css')
        js_path = os.path.join(project_root, 'assets', 'js', 'main.js')
        
        assert os.path.exists(css_path)
        assert os.path.exists(js_path)
        
        # Check file content
        with open(css_path, 'r') as f:
            css_content = f.read()
            assert len(css_content) > 0
            # Look for common CSS classes that should exist
            has_basic_styling = any(selector in css_content for selector in ['.card', '.header', '.btn', '.body'])
            assert has_basic_styling, f"CSS should contain basic styling classes. Found: {[selector for selector in ['.card', '.header', '.btn', '.body'] if selector in css_content]}"
        
        with open(js_path, 'r') as f:
            js_content = f.read()
            assert len(js_content) > 0
            assert 'function' in js_content or 'const' in js_content

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
