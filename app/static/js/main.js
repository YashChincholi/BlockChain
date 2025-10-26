document.addEventListener('DOMContentLoaded', function() {
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true
    });

    initHashTooltips();
    initAutoRefresh();
});

function initHashTooltips() {
    const hashFields = document.querySelectorAll('.hash-field');
    hashFields.forEach(field => {
        field.addEventListener('click', function() {
            const fullHash = this.getAttribute('title');
            if (fullHash) {
                copyToClipboard(fullHash);
                showToast('Hash copied to clipboard!');
            }
        });
    });
}

function initAutoRefresh() {
    const refreshInterval = 30000;

    setInterval(() => {
        if (window.location.pathname === '/') {
            fetchBlockchainStats();
        }
    }, refreshInterval);
}

async function fetchBlockchainStats() {
    try {
        const response = await fetch('/api/blockchain');
        const data = await response.json();

        if (data.success) {
            updateStats(data.stats);
        }
    } catch (error) {
        console.error('Error fetching blockchain stats:', error);
    }
}

function updateStats(stats) {
    const totalBlocksElement = document.querySelector('.stat-card:nth-child(1) h3');
    const chainStatusElement = document.querySelector('.stat-card:nth-child(2) h3');
    const lastHashElement = document.querySelector('.stat-card:nth-child(3) h3');
    const invalidBlocksElement = document.querySelector('.stat-card:nth-child(4) h3');

    if (totalBlocksElement) {
        totalBlocksElement.textContent = stats.total_blocks;
    }

    if (chainStatusElement) {
        chainStatusElement.textContent = stats.is_valid ? 'Valid' : 'Invalid';
    }

    if (lastHashElement && stats.last_block_hash) {
        lastHashElement.textContent = stats.last_block_hash.substring(0, 8) + '...';
    }

    if (invalidBlocksElement) {
        invalidBlocksElement.textContent = stats.invalid_blocks.length;
    }
}

function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).catch(err => {
            console.error('Failed to copy:', err);
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
    } catch (err) {
        console.error('Fallback copy failed:', err);
    }

    document.body.removeChild(textArea);
}

function showToast(message) {
    const existingToast = document.querySelector('.custom-toast');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = 'custom-toast';
    toast.innerHTML = `
        <i class="bi bi-check-circle-fill"></i>
        <span>${message}</span>
    `;

    const style = document.createElement('style');
    style.textContent = `
        .custom-toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #198754;
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 10000;
            animation: slideIn 0.3s ease-out, slideOut 0.3s ease-in 2.7s;
            font-weight: 600;
        }

        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;

    if (!document.querySelector('style[data-toast-style]')) {
        style.setAttribute('data-toast-style', 'true');
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

document.querySelectorAll('.block-card').forEach(card => {
    observer.observe(card);
});
