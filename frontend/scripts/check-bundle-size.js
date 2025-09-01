#!/usr/bin/env node
/**
 * Bundle Size Check Script
 * Validates that the application bundle size stays within acceptable limits
 */

const fs = require('fs');
const path = require('path');

// Bundle size limits (in bytes)
const BUNDLE_LIMITS = {
    // Main application bundle
    'index': 500 * 1024,        // 500KB for main app
    'vendor': 800 * 1024,       // 800KB for vendor libs
    'charts': 200 * 1024,       // 200KB for chart libraries
    'auth': 150 * 1024,         // 150KB for auth libraries
    'query': 100 * 1024,        // 100KB for react-query
    'dnd': 100 * 1024,          // 100KB for drag-and-drop
    'virtualization': 50 * 1024 // 50KB for virtualization
};

// Total bundle size limit
const TOTAL_BUNDLE_LIMIT = 2 * 1024 * 1024; // 2MB total

function getFileSizeInBytes(filePath) {
    try {
        const stats = fs.statSync(filePath);
        return stats.size;
    } catch (error) {
        return 0;
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function checkBundleSize() {
    console.log('📦 Bundle Size Analysis');
    console.log('=' * 50);

    const distPath = path.join(__dirname, '..', 'dist', 'assets');
    
    if (!fs.existsSync(distPath)) {
        console.error('❌ Build directory not found. Run "npm run build" first.');
        process.exit(1);
    }

    const files = fs.readdirSync(distPath);
    const bundles = {};
    let totalSize = 0;
    let errors = [];
    let warnings = [];

    // Analyze JavaScript files
    files.forEach(file => {
        if (file.endsWith('.js')) {
            const filePath = path.join(distPath, file);
            const size = getFileSizeInBytes(filePath);
            totalSize += size;

            // Determine bundle type based on filename
            let bundleType = 'other';
            if (file.includes('index')) bundleType = 'index';
            else if (file.includes('vendor')) bundleType = 'vendor';
            else if (file.includes('charts')) bundleType = 'charts';
            else if (file.includes('auth')) bundleType = 'auth';
            else if (file.includes('query')) bundleType = 'query';
            else if (file.includes('dnd')) bundleType = 'dnd';
            else if (file.includes('virtualization')) bundleType = 'virtualization';

            bundles[file] = {
                type: bundleType,
                size: size,
                sizeFormatted: formatBytes(size)
            };

            // Check against limits
            const limit = BUNDLE_LIMITS[bundleType];
            if (limit && size > limit) {
                errors.push(`${file} (${formatBytes(size)}) exceeds limit of ${formatBytes(limit)}`);
            } else if (limit && size > limit * 0.8) {
                warnings.push(`${file} (${formatBytes(size)}) approaching limit of ${formatBytes(limit)}`);
            }
        }
    });

    // Analyze CSS files
    files.forEach(file => {
        if (file.endsWith('.css')) {
            const filePath = path.join(distPath, file);
            const size = getFileSizeInBytes(filePath);
            totalSize += size;

            bundles[file] = {
                type: 'css',
                size: size,
                sizeFormatted: formatBytes(size)
            };

            // CSS should be small due to Tailwind purging
            if (size > 100 * 1024) { // 100KB limit for CSS
                warnings.push(`${file} (${formatBytes(size)}) is larger than expected for CSS`);
            }
        }
    });

    // Display results
    console.log('\n📊 Bundle Analysis:');
    console.log('-'.repeat(50));
    
    Object.entries(bundles)
        .sort((a, b) => b[1].size - a[1].size)
        .forEach(([filename, info]) => {
            const status = errors.some(e => e.includes(filename)) ? '❌' : 
                          warnings.some(w => w.includes(filename)) ? '⚠️' : '✅';
            console.log(`${status} ${filename}: ${info.sizeFormatted} (${info.type})`);
        });

    console.log(`\n📈 Total Bundle Size: ${formatBytes(totalSize)}`);
    
    // Check total size
    if (totalSize > TOTAL_BUNDLE_LIMIT) {
        errors.push(`Total bundle size (${formatBytes(totalSize)}) exceeds limit of ${formatBytes(TOTAL_BUNDLE_LIMIT)}`);
    } else if (totalSize > TOTAL_BUNDLE_LIMIT * 0.8) {
        warnings.push(`Total bundle size (${formatBytes(totalSize)}) approaching limit of ${formatBytes(TOTAL_BUNDLE_LIMIT)}`);
    }

    // Display warnings
    if (warnings.length > 0) {
        console.log('\n⚠️  Warnings:');
        warnings.forEach(warning => console.log(`  • ${warning}`));
    }

    // Display errors
    if (errors.length > 0) {
        console.log('\n❌ Errors:');
        errors.forEach(error => console.log(`  • ${error}`));
        console.log('\n🚨 Bundle size check failed!');
        console.log('Consider optimizing your bundles:');
        console.log('  • Use dynamic imports for less critical code');
        console.log('  • Check for duplicate dependencies');
        console.log('  • Analyze bundle with "npm run bundle-analyzer"');
        process.exit(1);
    }

    // Success
    if (warnings.length === 0) {
        console.log('\n✅ All bundle sizes are within limits!');
    } else {
        console.log('\n⚠️  Bundle sizes are within limits but some warnings exist.');
    }

    // Save results to JSON for CI/CD
    const results = {
        timestamp: new Date().toISOString(),
        totalSize: totalSize,
        totalSizeFormatted: formatBytes(totalSize),
        bundles: bundles,
        errors: errors,
        warnings: warnings,
        passed: errors.length === 0
    };

    fs.writeFileSync(
        path.join(__dirname, '..', 'dist', 'bundle-size-report.json'),
        JSON.stringify(results, null, 2)
    );

    console.log('\n💾 Report saved to dist/bundle-size-report.json');
}

if (require.main === module) {
    checkBundleSize();
}

module.exports = { checkBundleSize, BUNDLE_LIMITS, TOTAL_BUNDLE_LIMIT };