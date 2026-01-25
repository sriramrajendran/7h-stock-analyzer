// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
    // Set active nav link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.classList.remove('active');
        if ((currentPath === '/' && link.id === 'nav-portfolio') || 
            (currentPath === '/watchlist' && link.id === 'nav-watchlist') ||
            (currentPath === '/market' && link.id === 'nav-market') ||
            (currentPath === '/etf' && link.id === 'nav-etf') ||
            (currentPath === '/import_portfolio' && link.id === 'nav-import')) {
            link.classList.add('active');
        }
    });
    
    // Auto-load data based on page type
    const pageType = window.PAGE_TYPE || 
                    (currentPath === '/watchlist' ? 'watchlist' : 
                     currentPath === '/market' ? 'market' :
                     currentPath === '/etf' ? 'etf' :
                     currentPath === '/import_portfolio' ? 'import_portfolio' : 'portfolio');
    
    if (pageType === 'portfolio' || pageType === 'watchlist') {
        // Load config stocks and then auto-analyze
        const stocks = await loadConfigStocks();
        if (stocks && stocks.length > 0) {
            // Small delay to ensure form is ready
            setTimeout(() => {
                autoAnalyzePortfolio(stocks);
            }, 100);
        }
    } else if (pageType === 'market') {
        // Auto-analyze market
        setTimeout(() => {
            autoAnalyzeMarket();
        }, 100);
    } else if (pageType === 'etf') {
        // Auto-analyze ETFs
        setTimeout(() => {
            autoAnalyzeETF();
        }, 100);
    }
});

// Load stocks from config file
async function loadConfigStocks() {
    try {
        const pageType = window.PAGE_TYPE || 
                        (window.location.pathname === '/watchlist' ? 'watchlist' : 'portfolio');
        
        // Only load for portfolio/watchlist pages
        if (pageType !== 'market' && pageType !== 'etf') {
            const response = await fetch(`/api/config_stocks?type=${pageType}`);
            const data = await response.json();
            
            if (data.success && data.stocks.length > 0) {
                const symbolsTextarea = document.getElementById('symbols');
                if (symbolsTextarea) {
                    symbolsTextarea.value = data.stocks.join(', ');
                }
                return data.stocks;
            } else {
                const symbolsTextarea = document.getElementById('symbols');
                if (symbolsTextarea) {
                    symbolsTextarea.placeholder = 'No stocks found in config file. Edit files in input/ directory to update stock lists.';
                }
                return [];
            }
        }
        return [];
    } catch (error) {
        console.error('Error loading config stocks:', error);
        const symbolsTextarea = document.getElementById('symbols');
        if (symbolsTextarea) {
            symbolsTextarea.placeholder = 'Error loading config. Check files in input/ directory or enter stock symbols manually.';
        }
        return [];
    }
}

// Auto-analyze portfolio/watchlist
async function autoAnalyzePortfolio(stocks) {
    const symbols = stocks.join(', ');
    const period = document.getElementById('portfolio-period')?.value || '1y';
    const topN = parseInt(document.getElementById('top-n')?.value || '10');
    const resultsDiv = document.getElementById('portfolio-results');
    
    if (!symbols || symbols.trim() === '') {
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/analyze_portfolio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symbols, period, top_n: topN })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Portfolio analysis failed');
        }
        
        displayPortfolioResults(data, resultsDiv);
    } catch (error) {
        showError(resultsDiv, error.message);
    } finally {
        hideLoading();
    }
}

// Auto-analyze market
async function autoAnalyzeMarket() {
    const period = document.getElementById('market-period')?.value || '1y';
    const topN = parseInt(document.getElementById('market-top-n')?.value || '10');
    const resultsDiv = document.getElementById('portfolio-results');
    
    showLoading();
    
    try {
        const response = await fetch('/analyze_market', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ period, top_n: topN })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Market analysis failed');
        }
        
        displayMarketResults(data, resultsDiv);
    } catch (error) {
        showError(resultsDiv, error.message);
    } finally {
        hideLoading();
    }
}

// Auto-analyze ETF
async function autoAnalyzeETF() {
    const period = document.getElementById('market-period')?.value || '1y';
    const topN = parseInt(document.getElementById('market-top-n')?.value || '10');
    const resultsDiv = document.getElementById('portfolio-results');
    
    showLoading();
    
    try {
        const response = await fetch('/analyze_etf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ period, top_n: topN })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'ETF analysis failed');
        }
        
        displayMarketResults(data, resultsDiv);
    } catch (error) {
        showError(resultsDiv, error.message);
    } finally {
        hideLoading();
    }
}

// Portfolio/Watchlist Analysis
const portfolioForm = document.getElementById('portfolio-form');
if (portfolioForm) {
    portfolioForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const symbols = document.getElementById('symbols').value.trim();
    const period = document.getElementById('portfolio-period').value;
    const topN = parseInt(document.getElementById('top-n').value);
    const resultsDiv = document.getElementById('portfolio-results');
    
    if (!symbols) {
        showError(resultsDiv, 'Please enter stock symbols');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/analyze_portfolio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symbols, period, top_n: topN })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Portfolio analysis failed');
        }
        
        displayPortfolioResults(data, resultsDiv);
    } catch (error) {
        showError(resultsDiv, error.message);
    } finally {
        hideLoading();
    }
    });
}

// Market Analysis
const marketForm = document.getElementById('market-form');
if (marketForm) {
    marketForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const period = document.getElementById('market-period').value;
        const topN = parseInt(document.getElementById('market-top-n').value);
        const resultsDiv = document.getElementById('portfolio-results');
        
        showLoading();
        
        try {
            const response = await fetch('/analyze_market', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ period, top_n: topN })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Market analysis failed');
            }
            
            displayMarketResults(data, resultsDiv);
        } catch (error) {
            showError(resultsDiv, error.message);
        } finally {
            hideLoading();
        }
    });
}

// ETF Analysis
const etfForm = document.getElementById('etf-form');
if (etfForm) {
    etfForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const period = document.getElementById('market-period').value;
        const topN = parseInt(document.getElementById('market-top-n').value);
        const resultsDiv = document.getElementById('portfolio-results');
        
        showLoading();
        
        try {
            const response = await fetch('/analyze_etf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ period, top_n: topN })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'ETF analysis failed');
            }
            
            displayMarketResults(data, resultsDiv);
        } catch (error) {
            showError(resultsDiv, error.message);
        } finally {
            hideLoading();
        }
    });
}

// Portfolio Import
const importForm = document.getElementById('import-form');
if (importForm) {
    importForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fileInput = document.getElementById('csv-file');
        const broker = document.getElementById('broker-select').value;
        const saveToStorage = document.getElementById('save-storage').checked;
        const saveToConfig = document.getElementById('save-config').checked;
        
        if (!fileInput.files[0]) {
            showError('Please select a CSV file to import');
            return;
        }
        
        showLoading('Importing portfolio data...');
        
        try {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('broker', broker);
            formData.append('save_to_storage', saveToStorage);
            formData.append('save_to_config', saveToConfig);
            
            const response = await fetch('/api/import_portfolio', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                displayImportResults(result);
            } else {
                showError(result.error || 'Import failed');
            }
        } catch (error) {
            showError('Import failed: ' + error.message);
        } finally {
            hideLoading();
        }
    });
}


function displayPortfolioResults(data, container) {
    const { buy_stocks, sell_stocks, summary, failed_symbols } = data;
    
    let html = '<div class="results">';
    
    // Summary Statistics
    html += `
        <div class="result-section">
            <h3>Portfolio Summary</h3>
            <div class="portfolio-summary">
                <div class="summary-card">
                    <div class="summary-value">${summary.total}</div>
                    <div class="summary-label">Total Analyzed</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value" style="color: var(--success);">${summary.buy_count}</div>
                    <div class="summary-label">BUY Recommendations</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value" style="color: var(--danger);">${summary.sell_count}</div>
                    <div class="summary-label">SELL Recommendations</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value" style="color: var(--warning);">${summary.hold_count}</div>
                    <div class="summary-label">HOLD Recommendations</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${summary.avg_score}</div>
                    <div class="summary-label">Average Score</div>
                </div>
            </div>
        </div>
    `;
    
    // Top BUY Recommendations
    if (buy_stocks.length > 0) {
        html += `
            <div class="result-section">
                <h3 style="color: var(--success);">Top ${buy_stocks.length} BUY Recommendations</h3>
                <div class="table-wrapper">
                <table class="stocks-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Symbol</th>
                            <th>Price</th>
                            <th>1D %</th>
                            <th>1W %</th>
                            <th>1M %</th>
                            <th>6M %</th>
                            <th>1Y %</th>
                            <th>RSI</th>
                            <th>VCP</th>
                            <th>RSI Div</th>
                            <th>MACD Div</th>
                            <th>Cross</th>
                            <th>Breakout</th>
                        <th>Tip</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    ${buy_stocks.map((stock, idx) => `
                            <tr class="stock-row" data-symbol="${stock.symbol}" data-index="${idx}" onclick="showStockDetail('${stock.symbol}', ${idx})">
                                <td>${idx + 1}</td>
                                <td data-company="${stock.company}"><strong>${stock.symbol}</strong></td>
                                <td>$${stock.price.toFixed(2)}</td>
                                <td class="${stock.change_1d >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1d >= 0 ? '+' : ''}${stock.change_1d.toFixed(2)}%
                                </td>
                                <td class="${stock.change_1w >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1w >= 0 ? '+' : ''}${stock.change_1w.toFixed(2)}%
                                </td>
                                <td class="${stock.change_1m >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1m >= 0 ? '+' : ''}${stock.change_1m.toFixed(2)}%
                                </td>
                                <td class="${stock.change_6m >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_6m >= 0 ? '+' : ''}${stock.change_6m.toFixed(2)}%
                                </td>
                                <td class="${(stock.change_1y || 0) >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${(stock.change_1y || 0) >= 0 ? '+' : ''}${(stock.change_1y || 0).toFixed(2)}%
                                </td>
                                <td>${stock.rsi.toFixed(2)}</td>
                                <td>${getVCPBadge(stock.vcp_pattern)}</td>
                                <td>${getDivergenceBadge(stock.rsi_divergence)}</td>
                                <td>${getDivergenceBadge(stock.macd_divergence)}</td>
                                <td>${getCrossoverBadge(stock.enhanced_crossovers)}</td>
                                <td>${getBreakoutBadge(stock.breakout_setup)}</td>
                                <td><span class="recommendation-badge ${getRecommendationClass(stock.recommendation)}">${stock.recommendation}</span></td>
                                <td class="score-positive">${stock.score}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                </div>
            </div>
        `;
    } else {
        html += '<div class="result-section"><p class="info-text">No BUY recommendations found.</p></div>';
    }
    
    // Top SELL Recommendations
    if (sell_stocks.length > 0) {
        html += `
            <div class="result-section">
                <h3 style="color: var(--danger);">Top ${sell_stocks.length} SELL Recommendations</h3>
                <div class="table-wrapper">
                <table class="stocks-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Symbol</th>
                            <th>Price</th>
                            <th>1D %</th>
                            <th>1W %</th>
                            <th>1M %</th>
                            <th>6M %</th>
                            <th>1Y %</th>
                            <th>RSI</th>
                            <th>VCP</th>
                            <th>RSI Div</th>
                            <th>MACD Div</th>
                            <th>Cross</th>
                            <th>Breakout</th>
                        <th>Tip</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    ${sell_stocks.map((stock, idx) => `
                            <tr class="stock-row" data-symbol="${stock.symbol}" data-index="${buy_stocks.length + idx}" onclick="showStockDetail('${stock.symbol}', ${buy_stocks.length + idx})">
                                <td>${idx + 1}</td>
                                <td data-company="${stock.company}"><strong>${stock.symbol}</strong></td>
                                <td>$${stock.price.toFixed(2)}</td>
                                <td class="${stock.change_1d >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1d >= 0 ? '+' : ''}${stock.change_1d.toFixed(2)}%
                                </td>
                                <td class="${stock.change_1w >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1w >= 0 ? '+' : ''}${stock.change_1w.toFixed(2)}%
                                </td>
                                <td class="${stock.change_1m >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1m >= 0 ? '+' : ''}${stock.change_1m.toFixed(2)}%
                                </td>
                                <td class="${stock.change_6m >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_6m >= 0 ? '+' : ''}${stock.change_6m.toFixed(2)}%
                                </td>
                                <td class="${(stock.change_1y || 0) >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${(stock.change_1y || 0) >= 0 ? '+' : ''}${(stock.change_1y || 0).toFixed(2)}%
                                </td>
                                <td>${stock.rsi.toFixed(2)}</td>
                                <td>${getVCPBadge(stock.vcp_pattern)}</td>
                                <td>${getDivergenceBadge(stock.rsi_divergence)}</td>
                                <td>${getDivergenceBadge(stock.macd_divergence)}</td>
                                <td>${getCrossoverBadge(stock.enhanced_crossovers)}</td>
                                <td>${getBreakoutBadge(stock.breakout_setup)}</td>
                                <td><span class="recommendation-badge recommendation-sell">${stock.recommendation}</span></td>
                                <td class="score-negative">${stock.score}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                </div>
            </div>
        `;
    } else {
        html += '<div class="result-section"><p class="info-text">No SELL recommendations found.</p></div>';
    }
    
    // HOLD Recommendations
    if (data.hold_stocks && data.hold_stocks.length > 0) {
        html += `
            <div class="result-section">
                <h3 style="color: var(--warning);">HOLD Recommendations (${data.hold_stocks.length})</h3>
                <div class="table-wrapper">
                <table class="stocks-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Symbol</th>
                            <th>Price</th>
                            <th>1D %</th>
                            <th>1W %</th>
                            <th>1M %</th>
                            <th>6M %</th>
                            <th>1Y %</th>
                            <th>RSI</th>
                            <th>VCP</th>
                            <th>RSI Div</th>
                            <th>MACD Div</th>
                            <th>Cross</th>
                            <th>Breakout</th>
                        <th>Tip</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.hold_stocks.map((stock, idx) => `
                            <tr class="stock-row" data-symbol="${stock.symbol}" data-index="${buy_stocks.length + sell_stocks.length + idx}" onclick="showStockDetail('${stock.symbol}', ${buy_stocks.length + sell_stocks.length + idx})">
                                <td>${idx + 1}</td>
                                <td data-company="${stock.company}"><strong>${stock.symbol}</strong></td>
                                <td>$${stock.price.toFixed(2)}</td>
                                <td class="${stock.change_1d >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1d >= 0 ? '+' : ''}${stock.change_1d.toFixed(2)}%
                                </td>
                                <td class="${stock.change_1w >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1w >= 0 ? '+' : ''}${stock.change_1w.toFixed(2)}%
                                </td>
                                <td class="${stock.change_1m >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1m >= 0 ? '+' : ''}${stock.change_1m.toFixed(2)}%
                                </td>
                                <td class="${stock.change_6m >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_6m >= 0 ? '+' : ''}${stock.change_6m.toFixed(2)}%
                                </td>
                                <td class="${(stock.change_1y || 0) >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${(stock.change_1y || 0) >= 0 ? '+' : ''}${(stock.change_1y || 0).toFixed(2)}%
                                </td>
                                <td>${stock.rsi.toFixed(2)}</td>
                                <td>${getVCPBadge(stock.vcp_pattern)}</td>
                                <td>${getDivergenceBadge(stock.rsi_divergence)}</td>
                                <td>${getDivergenceBadge(stock.macd_divergence)}</td>
                                <td>${getCrossoverBadge(stock.enhanced_crossovers)}</td>
                                <td>${getBreakoutBadge(stock.breakout_setup)}</td>
                                <td><span class="recommendation-badge recommendation-hold">${stock.recommendation}</span></td>
                                <td style="color: var(--warning);">${stock.score}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                </div>
            </div>
        `;
    } else {
        html += '<div class="result-section"><p class="info-text">No HOLD recommendations found.</p></div>';
    }
    
    // Store all stocks for detail view
    window.allStocks = [...(buy_stocks || []), ...(sell_stocks || []), ...(data.hold_stocks || [])];
    
    // Failed symbols
    if (failed_symbols && failed_symbols.length > 0) {
        html += `
            <div class="error-message">
                <strong>Failed to analyze:</strong> ${failed_symbols.join(', ')}
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function displayMarketResults(data, container) {
    const { buy_recommendations, total_analyzed, failed_symbols } = data;
    
    let html = '<div class="results">';
    
    html += `
        <div class="result-section">
            <h3>Top ${buy_recommendations.length} BUY Recommendations</h3>
            <p class="info-text">Analyzed ${total_analyzed} stocks from US market</p>
            <div class="table-wrapper">
            <table class="stocks-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Symbol</th>
                        <th>Price</th>
                        <th>1D %</th>
                        <th>1W %</th>
                        <th>1M %</th>
                        <th>6M %</th>
                        <th>1Y %</th>
                        <th>RSI</th>
                        <th>VCP</th>
                        <th>RSI Div</th>
                        <th>MACD Div</th>
                        <th>Cross</th>
                        <th>Breakout</th>
                        <th>Tip</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    ${buy_recommendations.map((stock, idx) => `
                            <tr class="stock-row" data-symbol="${stock.symbol}" data-index="${idx}" onclick="showStockDetail('${stock.symbol}', ${idx})">
                                <td>${idx + 1}</td>
                                <td data-company="${stock.company}"><strong>${stock.symbol}</strong></td>
                                <td>$${stock.price.toFixed(2)}</td>
                                <td class="${stock.change_1d >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1d >= 0 ? '+' : ''}${stock.change_1d.toFixed(2)}%
                                </td>
                                <td class="${stock.change_1w >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1w >= 0 ? '+' : ''}${stock.change_1w.toFixed(2)}%
                                </td>
                                <td class="${stock.change_1m >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1m >= 0 ? '+' : ''}${stock.change_1m.toFixed(2)}%
                                </td>
                                <td class="${stock.change_6m >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_6m >= 0 ? '+' : ''}${stock.change_6m.toFixed(2)}%
                                </td>
                                <td class="${(stock.change_1y || 0) >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${(stock.change_1y || 0) >= 0 ? '+' : ''}${(stock.change_1y || 0).toFixed(2)}%
                                </td>
                                <td>${stock.rsi.toFixed(2)}</td>
                                <td>${getVCPBadge(stock.vcp_pattern)}</td>
                                <td>${getDivergenceBadge(stock.rsi_divergence)}</td>
                                <td>${getDivergenceBadge(stock.macd_divergence)}</td>
                                <td>${getCrossoverBadge(stock.enhanced_crossovers)}</td>
                                <td>${getBreakoutBadge(stock.breakout_setup)}</td>
                                <td><span class="recommendation-badge recommendation-buy">${stock.recommendation}</span></td>
                                <td class="score-positive">${stock.score}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    
    // Store stocks for detail view
    window.allStocks = buy_recommendations || [];
    
    if (failed_symbols && failed_symbols.length > 0) {
        html += `
            <div class="error-message">
                <strong>Failed to analyze:</strong> ${failed_symbols.slice(0, 10).join(', ')}${failed_symbols.length > 10 ? '...' : ''}
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

// Store stocks data globally for detail view
let stockDetailsCache = {};

function showStockDetail(symbol, index) {
    const stocks = window.allStocks || [];
    const stock = stocks[index];
    
    if (!stock) return;
    
    const detailModal = document.getElementById('stock-detail-modal');
    if (detailModal) {
        detailModal.remove();
    }
    
    const fundamental = stock.fundamental || {};
    
    const modal = document.createElement('div');
    modal.id = 'stock-detail-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>${symbol} - ${stock.company}</h2>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="analysis-container">
                    <div class="analysis-section">
                        <h3>Technical Analysis</h3>
                        <div class="indicators-grid">
                            <div class="indicator-card">
                                <div class="indicator-label">Current Price</div>
                                <div class="indicator-value">$${stock.price.toFixed(2)}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">1D Change</div>
                                <div class="indicator-value ${stock.change_1d >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1d >= 0 ? '+' : ''}${stock.change_1d.toFixed(2)}%
                                </div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">1W Change</div>
                                <div class="indicator-value ${stock.change_1w >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1w >= 0 ? '+' : ''}${stock.change_1w.toFixed(2)}%
                                </div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">1M Change</div>
                                <div class="indicator-value ${stock.change_1m >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_1m >= 0 ? '+' : ''}${stock.change_1m.toFixed(2)}%
                                </div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">6M Change</div>
                                <div class="indicator-value ${stock.change_6m >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${stock.change_6m >= 0 ? '+' : ''}${stock.change_6m.toFixed(2)}%
                                </div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">1Y Change</div>
                                <div class="indicator-value ${(stock.change_1y || 0) >= 0 ? 'score-positive' : 'score-negative'}">
                                    ${(stock.change_1y || 0) >= 0 ? '+' : ''}${(stock.change_1y || 0).toFixed(2)}%
                                </div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">RSI (14)</div>
                                <div class="indicator-value">${stock.rsi.toFixed(2)}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">MACD</div>
                                <div class="indicator-value">${stock.macd ? stock.macd.toFixed(2) : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">SMA (20)</div>
                                <div class="indicator-value">${stock.sma_20 ? '$' + stock.sma_20.toFixed(2) : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">SMA (50)</div>
                                <div class="indicator-value">${stock.sma_50 ? '$' + stock.sma_50.toFixed(2) : 'N/A'}</div>
                            </div>
                        </div>
                        <div style="margin-top: 20px;">
                            <strong>Recommendation:</strong> 
                            <span class="recommendation-badge ${getRecommendationClass(stock.recommendation)}">${stock.recommendation}</span>
                            <strong style="margin-left: 15px;">Score:</strong> 
                            <span class="${stock.score >= 0 ? 'score-positive' : 'score-negative'}">${stock.score}</span>
                        </div>
                        <h4 style="margin-top: 15px;">Reasoning:</h4>
                        <ul class="reasoning-list">
                            ${(stock.reasoning || []).map(reason => `<li>${reason}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="analysis-section">
                        <h3>Fundamental Analysis</h3>
                        <div class="indicators-grid">
                            <div class="indicator-card">
                                <div class="indicator-label">P/E Ratio</div>
                                <div class="indicator-value">${fundamental.pe_ratio !== undefined ? fundamental.pe_ratio : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">Forward P/E</div>
                                <div class="indicator-value">${fundamental.forward_pe !== undefined ? fundamental.forward_pe : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">P/B Ratio</div>
                                <div class="indicator-value">${fundamental.pb_ratio !== undefined ? fundamental.pb_ratio : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">Dividend Yield</div>
                                <div class="indicator-value">${fundamental.dividend_yield !== undefined ? fundamental.dividend_yield + '%' : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">Market Cap</div>
                                <div class="indicator-value">${fundamental.market_cap || 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">EPS</div>
                                <div class="indicator-value">${fundamental.eps !== undefined ? '$' + fundamental.eps : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">Revenue Growth</div>
                                <div class="indicator-value">${fundamental.revenue_growth !== undefined ? fundamental.revenue_growth + '%' : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">Earnings Growth</div>
                                <div class="indicator-value">${fundamental.earnings_growth !== undefined ? fundamental.earnings_growth + '%' : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">ROE</div>
                                <div class="indicator-value">${fundamental.roe !== undefined ? fundamental.roe + '%' : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">Profit Margin</div>
                                <div class="indicator-value">${fundamental.profit_margin !== undefined ? fundamental.profit_margin + '%' : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">Debt to Equity</div>
                                <div class="indicator-value">${fundamental.debt_to_equity !== undefined ? fundamental.debt_to_equity : 'N/A'}</div>
                            </div>
                            <div class="indicator-card">
                                <div class="indicator-label">Beta</div>
                                <div class="indicator-value">${fundamental.beta !== undefined ? fundamental.beta : 'N/A'}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="analysis-section advanced-section">
                    <h3>Advanced Pattern Analysis</h3>
                    <div class="patterns-grid">
                        <div class="pattern-card">
                            <div class="pattern-title">VCP Pattern</div>
                            <div class="pattern-details">
                                ${getVCPDetails(stock.vcp_pattern)}
                            </div>
                        </div>
                        <div class="pattern-card">
                            <div class="pattern-title">RSI Divergence</div>
                            <div class="pattern-details">
                                ${getDivergenceDetails(stock.rsi_divergence, 'RSI')}
                            </div>
                        </div>
                        <div class="pattern-card">
                            <div class="pattern-title">MACD Divergence</div>
                            <div class="pattern-details">
                                ${getDivergenceDetails(stock.macd_divergence, 'MACD')}
                            </div>
                        </div>
                        <div class="pattern-card">
                            <div class="pattern-title">Enhanced Crossovers</div>
                            <div class="pattern-details">
                                ${getCrossoverDetails(stock.enhanced_crossovers)}
                            </div>
                        </div>
                        <div class="pattern-card">
                            <div class="pattern-title">Breakout Setup</div>
                            <div class="pattern-details">
                                ${getBreakoutDetails(stock.breakout_setup)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Close on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // Close on ESC key press
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);
}

function displayImportResults(data) {
    const resultsDiv = document.getElementById('portfolio-results');
    const { portfolio, summary, broker, total_holdings, config_save, storage_save } = data;
    
    let html = '<div class="results">';
    
    // Import Summary
    html += `
        <div class="result-section">
            <h3>Import Successful! 🎉</h3>
            <div class="import-summary">
                <div class="summary-card">
                    <div class="summary-value">${total_holdings}</div>
                    <div class="summary-label">Holdings Imported</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${broker.toUpperCase()}</div>
                    <div class="summary-label">Brokerage</div>
                </div>
                ${summary ? `
                <div class="summary-card">
                    <div class="summary-value">$${summary.total_equity_value.toLocaleString()}</div>
                    <div class="summary-label">Total Value</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value" style="color: ${summary.total_gain_loss >= 0 ? 'var(--success)' : 'var(--danger)'}">
                        ${summary.total_gain_loss >= 0 ? '+' : ''}$${summary.total_gain_loss.toLocaleString()}
                    </div>
                    <div class="summary-label">Total P&L</div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
    
    // Storage Save Status
    if (storage_save) {
        if (storage_save.success) {
            html += `
                <div class="result-section">
                    <div class="success-message">
                        ✅ Portfolio data saved for persistence
                        <br><small>File: ${storage_save.storage_file}</small>
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="result-section">
                    <div class="warning-message">
                        ⚠️ Portfolio imported but failed to save to storage: ${storage_save.error}
                    </div>
                </div>
            `;
        }
    }
    
    // Portfolio Holdings
    if (portfolio && portfolio.length > 0) {
        html += `
            <div class="result-section">
                <h3>Imported Holdings</h3>
                <div class="stock-grid">
        `;
        
        portfolio.slice(0, 10).forEach(holding => {
            const gainClass = holding.gain_loss >= 0 ? 'positive' : 'negative';
            const gainSign = holding.gain_loss >= 0 ? '+' : '';
            
            html += `
                <div class="stock-card">
                    <div class="stock-header">
                        <div class="stock-symbol">${holding.symbol}</div>
                        <div class="stock-broker">${holding.broker}</div>
                    </div>
                    <div class="stock-details">
                        <div class="stock-price">$${holding.current_price.toFixed(2)}</div>
                        <div class="stock-quantity">Qty: ${holding.quantity}</div>
                        <div class="stock-cost">Avg Cost: $${holding.average_cost.toFixed(2)}</div>
                        <div class="stock-value">Value: $${holding.equity_value.toFixed(2)}</div>
                        <div class="stock-gain ${gainClass}">
                            ${gainSign}$${holding.gain_loss.toFixed(2)} (${gainSign}${holding.gain_loss_pct.toFixed(2)}%)
                        </div>
                    </div>
                </div>
            `;
        });
        
        if (portfolio.length > 10) {
            html += `<div class="more-holdings">... and ${portfolio.length - 10} more holdings</div>`;
        }
        
        html += '</div></div>';
    }
    
    // Config Save Status
    if (config_save) {
        if (config_save.success) {
            html += `
                <div class="result-section">
                    <div class="success-message">
                        ✅ ${config_save.symbols_saved} symbols saved to portfolio configuration
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="result-section">
                    <div class="warning-message">
                        ⚠️ Portfolio imported but failed to save to config: ${config_save.error}
                    </div>
                </div>
            `;
        }
    }
    
    html += '</div>';
    resultsDiv.innerHTML = html;
}

// Make function available globally
window.showStockDetail = showStockDetail;

function getRecommendationClass(recommendation) {
    if (recommendation.includes('STRONG BUY')) {
        return 'recommendation-strong-buy';
    } else if (recommendation.includes('BUY')) {
        return 'recommendation-buy';
    } else if (recommendation.includes('SELL')) {
        return 'recommendation-sell';
    } else {
        return 'recommendation-hold';
    }
}

function getVCPBadge(vcp_pattern) {
    if (!vcp_pattern || vcp_pattern.pattern === 'INSUFFICIENT_DATA') {
        return '<span class="pattern-badge pattern-insufficient">N/A</span>';
    }
    
    switch (vcp_pattern.pattern) {
        case 'STRONG_VCP':
            return '<span class="pattern-badge pattern-strong-vcp" title="Strong Volatility Contraction Pattern">VCP</span>';
        case 'WEAK_VCP':
            return '<span class="pattern-badge pattern-weak-vcp" title="Weak Volatility Contraction Pattern">VCP</span>';
        default:
            return '<span class="pattern-badge pattern-none">-</span>';
    }
}

function getDivergenceBadge(divergence) {
    if (!divergence || divergence.divergence === 'INSUFFICIENT_DATA') {
        return '<span class="pattern-badge pattern-insufficient">N/A</span>';
    }
    
    switch (divergence.divergence) {
        case 'BULLISH':
            return '<span class="pattern-badge pattern-bullish" title="Bullish Divergence">↑</span>';
        case 'BEARISH':
            return '<span class="pattern-badge pattern-bearish" title="Bearish Divergence">↓</span>';
        default:
            return '<span class="pattern-badge pattern-none">-</span>';
    }
}

function getCrossoverBadge(crossovers) {
    if (!crossovers || !crossovers.crossovers || crossovers.crossovers.length === 0) {
        return '<span class="pattern-badge pattern-none">-</span>';
    }
    
    const volume_confirmed = crossovers.volume_confirmed || [];
    const total_crosses = crossovers.crossovers.length;
    const confirmed_crosses = volume_confirmed.length;
    
    if (confirmed_crosses > 0) {
        return `<span class="pattern-badge pattern-confirmed" title="${confirmed_crosses} volume-confirmed crossovers">✓${confirmed_crosses}</span>`;
    } else if (total_crosses > 0) {
        return `<span class="pattern-badge pattern-unconfirmed" title="${total_crosses} crossovers (no volume confirmation)">◯${total_crosses}</span>`;
    }
    
    return '<span class="pattern-badge pattern-none">-</span>';
}

function getBreakoutBadge(setup) {
    if (!setup || setup.qualified === undefined) {
        return '<span class="pattern-badge pattern-insufficient">N/A</span>';
    }
    const s = setup.strength || 0;
    if (setup.qualified) {
        return `<span class=\"pattern-badge pattern-confirmed\" title=\"Qualified breakout setup (strength ${s})\">✓${s}</span>`;
    }
    if (setup.prequalified) {
        return `<span class=\"pattern-badge pattern-weak-vcp\" title=\"Pre-breakout setup: all checks except breakout met (strength ${s})\">◔${s}</span>`;
    }
    return '<span class="pattern-badge pattern-unconfirmed" title="Breakout setup not qualified">◯</span>';
}

function getVCPDetails(vcp_pattern) {
    if (!vcp_pattern || vcp_pattern.pattern === 'INSUFFICIENT_DATA') {
        return '<div class="pattern-status pattern-insufficient">Insufficient data</div>';
    }
    
    const pattern = vcp_pattern.pattern;
    const strength = vcp_pattern.strength || 0;
    const details = vcp_pattern.details || [];
    
    let html = `<div class="pattern-status ${getVCPStatusClass(pattern)}">${getVCPStatusText(pattern)}</div>`;
    html += `<div class="pattern-strength">Strength: ${strength}/5</div>`;
    
    if (details.length > 0) {
        html += '<div class="pattern-indicators"><strong>Indicators:</strong><ul>';
        details.forEach(detail => {
            html += `<li>${detail}</li>`;
        });
        html += '</ul></div>';
    }
    
    return html;
}

function getBreakoutDetails(setup) {
    if (!setup || setup.qualified === undefined) {
        return '<div class="pattern-status pattern-insufficient">Insufficient data</div>';
    }
    const qualified = !!setup.qualified;
    const prequalified = !!setup.prequalified;
    const strength = setup.strength || 0;
    const details = setup.details || [];
    const checks = setup.checks || {};
    let statusClass = qualified ? 'pattern-confirmed' : (prequalified ? 'pattern-weak-vcp' : 'pattern-unconfirmed');
    let statusText = qualified ? 'Qualified Breakout Setup' : (prequalified ? 'Pre-Breakout Setup' : 'Not Qualified');
    let html = `<div class=\"pattern-status ${statusClass}\">${statusText}</div>`;
    html += `<div class="pattern-strength">Strength: ${strength}/6</div>`;
    if (details.length > 0) {
        html += '<div class="pattern-indicators"><strong>Checks:</strong><ul>';
        details.forEach(d => {
            html += `<li>${d}</li>`;
        });
        html += '</ul></div>';
    }
    // Render explicit check statuses if available
    const labels = {
        trend_ok: 'Trend alignment (Price > SMA50 [and SMA50 > SMA200 if available])',
        rsi_ok: 'RSI > 50',
        shrinking_pullbacks: 'Shrinking pullbacks',
        declining_volume: 'Declining consolidation volume',
        breakout_high_volume: 'Breakout above 20D high with volume'
    };
    const keys = Object.keys(labels);
    if (Object.keys(checks).length > 0) {
        html += '<div class="pattern-indicators"><strong>Check Status:</strong><ul>';
        keys.forEach(k => {
            if (k in checks) {
                html += `<li>${labels[k]}: ${checks[k] ? '✓' : '✗'}</li>`;
            }
        });
        html += '</ul></div>';
    }
    return html;
}

function getDivergenceDetails(divergence, type) {
    if (!divergence || divergence.divergence === 'INSUFFICIENT_DATA') {
        return '<div class="pattern-status pattern-insufficient">Insufficient data</div>';
    }
    
    const divType = divergence.divergence;
    const strength = divergence.strength || 0;
    
    let html = `<div class="pattern-status ${getDivergenceStatusClass(divType)}">${getDivergenceStatusText(divType)}</div>`;
    html += `<div class="pattern-strength">Strength: ${strength}/5</div>`;
    
    if (divType !== 'NONE') {
        html += `<div class="pattern-description">${getDivergenceDescription(divType, type)}</div>`;
    }
    
    return html;
}

function getCrossoverDetails(crossovers) {
    if (!crossovers || !crossovers.crossovers || crossovers.crossovers.length === 0) {
        return '<div class="pattern-status pattern-none">No crossovers detected</div>';
    }
    
    const all_crosses = crossovers.crossovers || [];
    const volume_confirmed = crossovers.volume_confirmed || [];
    const strength = crossovers.strength || 0;
    
    let html = `<div class="pattern-status pattern-confirmed">${all_crosses.length} crossovers found</div>`;
    html += `<div class="pattern-strength">Volume confirmed: ${volume_confirmed.length}/${all_crosses.length}</div>`;
    
    if (all_crosses.length > 0) {
        html += '<div class="pattern-indicators"><strong>Recent crossovers:</strong><ul>';
        all_crosses.slice(-3).forEach(cross => {
            const type = cross.includes('BULLISH') ? 'BULL' : 'BEAR';
            const confirmed = volume_confirmed.includes(cross) ? ' ✓' : '';
            html += `<li>${type} ${cross.replace('_', ' ')}${confirmed}</li>`;
        });
        html += '</ul></div>';
    }
    
    return html;
}

function getVCPStatusClass(pattern) {
    switch (pattern) {
        case 'STRONG_VCP': return 'pattern-strong-vcp';
        case 'WEAK_VCP': return 'pattern-weak-vcp';
        default: return 'pattern-none';
    }
}

function getVCPStatusText(pattern) {
    switch (pattern) {
        case 'STRONG_VCP': return 'Strong VCP Detected';
        case 'WEAK_VCP': return 'Weak VCP Detected';
        default: return 'No VCP Pattern';
    }
}

function getDivergenceStatusClass(divType) {
    switch (divType) {
        case 'BULLISH': return 'pattern-bullish';
        case 'BEARISH': return 'pattern-bearish';
        default: return 'pattern-none';
    }
}

function getDivergenceStatusText(divType) {
    switch (divType) {
        case 'BULLISH': return 'Bullish Divergence';
        case 'BEARISH': return 'Bearish Divergence';
        default: return 'No Divergence';
    }
}

function getDivergenceDescription(divType, indicator) {
    switch (divType) {
        case 'BULLISH':
            return `Price making lower lows while ${indicator} making higher lows - potential upward reversal`;
        case 'BEARISH':
            return `Price making higher highs while ${indicator} making lower highs - potential downward reversal`;
        default:
            return '';
    }
}

function showError(container, message) {
    if (typeof container === 'string') {
        // If container is a string, show as alert
        alert(message);
        return;
    }
    
    if (!container) {
        // If no container, use results div or alert
        const resultsDiv = document.getElementById('portfolio-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = `<div class="error-message">${message}</div>`;
        } else {
            alert(message);
        }
        return;
    }
    
    container.innerHTML = `<div class="error-message">${message}</div>`;
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

