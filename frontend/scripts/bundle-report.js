#!/usr/bin/env node
/**
 * Bundle Report Generator
 * Generates comprehensive bundle analysis and optimization recommendations
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function generateBundleReport() {
    console.log('📊 Generating Comprehensive Bundle Report');
    console.log('=' * 60);

    const distPath = path.join(__dirname, '..', 'dist');
    const assetsPath = path.join(distPath, 'assets');
    
    if (!fs.existsSync(distPath)) {
        console.error('❌ Build directory not found. Run "npm run build" first.');
        process.exit(1);
    }

    const report = {
        timestamp: new Date().toISOString(),
        build_info: getBuildInfo(),
        assets: analyzeAssets(assetsPath),
        recommendations: [],
        performance_score: 0
    };

    // Calculate performance score
    report.performance_score = calculatePerformanceScore(report.assets);
    
    // Generate recommendations
    report.recommendations = generateRecommendations(report.assets);

    // Save detailed report
    fs.writeFileSync(
        path.join(distPath, 'bundle-analysis-report.json'),
        JSON.stringify(report, null, 2)
    );

    // Generate human-readable report
    generateReadableReport(report);

    console.log('\n✅ Bundle report generated successfully!');
    console.log(`📄 JSON Report: dist/bundle-analysis-report.json`);
    console.log(`📝 Text Report: dist/bundle-analysis-report.txt`);
}

function getBuildInfo() {
    const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
    
    return {
        name: packageJson.name,
        version: packageJson.version,
        build_time: new Date().toISOString(),
        node_version: process.version,
        platform: process.platform
    };
}

function analyzeAssets(assetsPath) {
    const files = fs.existsSync(assetsPath) ? fs.readdirSync(assetsPath) : [];
    const assets = {
        javascript: [],
        css: [],
        other: [],
        total_size: 0,
        gzipped_estimate: 0
    };

    files.forEach(file => {
        const filePath = path.join(assetsPath, file);
        const stats = fs.statSync(filePath);
        const size = stats.size;
        
        const asset = {
            filename: file,
            size: size,
            size_formatted: formatBytes(size),
            gzipped_estimate: Math.round(size * 0.3), // Rough gzip estimate
            type: getAssetType(file),
            chunk_name: getChunkName(file)
        };

        assets.total_size += size;
        assets.gzipped_estimate += asset.gzipped_estimate;

        if (file.endsWith('.js')) {
            assets.javascript.push(asset);
        } else if (file.endsWith('.css')) {
            assets.css.push(asset);
        } else {
            assets.other.push(asset);
        }
    });

    // Sort by size (largest first)
    assets.javascript.sort((a, b) => b.size - a.size);
    assets.css.sort((a, b) => b.size - a.size);
    assets.other.sort((a, b) => b.size - a.size);

    assets.total_size_formatted = formatBytes(assets.total_size);
    assets.gzipped_estimate_formatted = formatBytes(assets.gzipped_estimate);

    return assets;
}

function getAssetType(filename) {
    if (filename.includes('vendor')) return 'vendor';
    if (filename.includes('index')) return 'main';
    if (filename.includes('charts')) return 'charts';
    if (filename.includes('auth')) return 'auth';
    if (filename.includes('query')) return 'query';
    if (filename.includes('dnd')) return 'drag-drop';
    if (filename.includes('virtualization')) return 'virtualization';
    return 'other';
}

function getChunkName(filename) {
    const match = filename.match(/^([^-]+)/);
    return match ? match[1] : 'unknown';
}

function calculatePerformanceScore(assets) {
    let score = 100;
    
    // Deduct points for large bundles
    if (assets.total_size > 2 * 1024 * 1024) score -= 30; // 2MB
    else if (assets.total_size > 1.5 * 1024 * 1024) score -= 20; // 1.5MB
    else if (assets.total_size > 1 * 1024 * 1024) score -= 10; // 1MB
    
    // Deduct points for large individual chunks
    assets.javascript.forEach(asset => {
        if (asset.size > 500 * 1024) score -= 10; // 500KB
        else if (asset.size > 300 * 1024) score -= 5; // 300KB
    });
    
    // Deduct points if CSS is too large
    const totalCssSize = assets.css.reduce((sum, asset) => sum + asset.size, 0);
    if (totalCssSize > 100 * 1024) score -= 10; // 100KB CSS
    
    return Math.max(score, 0);
}

function generateRecommendations(assets) {
    const recommendations = [];
    
    // Check total bundle size
    if (assets.total_size > 2 * 1024 * 1024) {
        recommendations.push({
            type: 'critical',
            message: 'Total bundle size exceeds 2MB. Consider aggressive code splitting.',
            action: 'Implement lazy loading for non-critical routes and components'
        });
    } else if (assets.total_size > 1.5 * 1024 * 1024) {
        recommendations.push({
            type: 'warning',
            message: 'Total bundle size is approaching 2MB limit.',
            action: 'Consider code splitting for large components'
        });
    }
    
    // Check individual JavaScript bundles
    assets.javascript.forEach(asset => {
        if (asset.size > 500 * 1024) {
            recommendations.push({
                type: 'warning',
                message: `${asset.filename} is large (${asset.size_formatted})`,
                action: `Consider splitting this chunk or removing unused dependencies`
            });
        }
    });
    
    // Check vendor bundle specifically
    const vendorBundle = assets.javascript.find(asset => asset.type === 'vendor');
    if (vendorBundle && vendorBundle.size > 800 * 1024) {
        recommendations.push({
            type: 'info',
            message: 'Vendor bundle is large. Check for duplicate dependencies.',
            action: 'Use bundle analyzer to identify optimization opportunities'
        });
    }
    
    // Check CSS size
    const totalCssSize = assets.css.reduce((sum, asset) => sum + asset.size, 0);
    if (totalCssSize > 100 * 1024) {
        recommendations.push({
            type: 'info',
            message: `CSS size is ${formatBytes(totalCssSize)}. Ensure Tailwind purging is working.`,
            action: 'Check Tailwind configuration and purge settings'
        });
    }
    
    // General optimization recommendations
    if (assets.javascript.length > 10) {
        recommendations.push({
            type: 'info',
            message: 'Many JavaScript chunks detected.',
            action: 'Consider consolidating some chunks to reduce HTTP requests'
        });
    }
    
    return recommendations;
}

function generateReadableReport(report) {
    const lines = [];
    
    lines.push('📦 BUNDLE ANALYSIS REPORT');
    lines.push('=' * 60);
    lines.push('');
    
    // Build info
    lines.push('🔧 Build Information:');
    lines.push(`   Project: ${report.build_info.name} v${report.build_info.version}`);
    lines.push(`   Build Time: ${report.build_info.build_time}`);
    lines.push(`   Node Version: ${report.build_info.node_version}`);
    lines.push('');
    
    // Performance score
    const scoreEmoji = report.performance_score >= 90 ? '🟢' : 
                      report.performance_score >= 70 ? '🟡' : '🔴';
    lines.push(`📊 Performance Score: ${scoreEmoji} ${report.performance_score}/100`);
    lines.push('');
    
    // Asset summary
    lines.push('📈 Bundle Summary:');
    lines.push(`   Total Size: ${report.assets.total_size_formatted}`);
    lines.push(`   Gzipped (est.): ${report.assets.gzipped_estimate_formatted}`);
    lines.push(`   JavaScript Files: ${report.assets.javascript.length}`);
    lines.push(`   CSS Files: ${report.assets.css.length}`);
    lines.push('');
    
    // JavaScript assets
    if (report.assets.javascript.length > 0) {
        lines.push('📜 JavaScript Assets:');
        report.assets.javascript.forEach(asset => {
            lines.push(`   ${asset.filename}: ${asset.size_formatted} (${asset.type})`);
        });
        lines.push('');
    }
    
    // CSS assets
    if (report.assets.css.length > 0) {
        lines.push('🎨 CSS Assets:');
        report.assets.css.forEach(asset => {
            lines.push(`   ${asset.filename}: ${asset.size_formatted}`);
        });
        lines.push('');
    }
    
    // Recommendations
    if (report.recommendations.length > 0) {
        lines.push('💡 Optimization Recommendations:');
        report.recommendations.forEach((rec, index) => {
            const emoji = rec.type === 'critical' ? '🚨' : 
                         rec.type === 'warning' ? '⚠️' : 'ℹ️';
            lines.push(`   ${emoji} ${rec.message}`);
            lines.push(`      Action: ${rec.action}`);
            if (index < report.recommendations.length - 1) lines.push('');
        });
        lines.push('');
    }
    
    // Next steps
    lines.push('🚀 Next Steps:');
    lines.push('   1. Run "npm run bundle-analyzer" for detailed analysis');
    lines.push('   2. Check for unused dependencies with "npm-check"');
    lines.push('   3. Consider implementing lazy loading for large components');
    lines.push('   4. Monitor bundle size in CI/CD pipeline');
    
    const reportContent = lines.join('\n');
    fs.writeFileSync(
        path.join(__dirname, '..', 'dist', 'bundle-analysis-report.txt'),
        reportContent
    );
    
    // Also display to console
    console.log('\n' + reportContent);
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

if (require.main === module) {
    generateBundleReport();
}

module.exports = { generateBundleReport };