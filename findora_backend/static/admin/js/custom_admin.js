/**
 * Findora Custom Admin Panel Interaction JS
 * Provides sidebar toggling, live table filtering, and shortcut navigation.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ─── 1. Hamburger Sidebar Toggle ─────────────────────────────────────────
    const hamburgerBtn = document.getElementById('findora-hamburger-toggle');
    const body = document.body;

    // Load saved sidebar preference
    const isCollapsed = localStorage.getItem('findora_sidebar_collapsed') === 'true';
    if (isCollapsed) {
        body.classList.add('sidebar-collapsed');
    }

    if (hamburgerBtn) {
        hamburgerBtn.addEventListener('click', (e) => {
            e.preventDefault();
            body.classList.toggle('sidebar-collapsed');
            const nowCollapsed = body.classList.contains('sidebar-collapsed');
            localStorage.setItem('findora_sidebar_collapsed', nowCollapsed);
        });
    }

    // ─── 2. Global Shortcut (Ctrl+K or Cmd+K) ─────────────────────────────────
    const globalSearchInput = document.getElementById('findora-global-search');
    
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (globalSearchInput) {
                globalSearchInput.focus();
                globalSearchInput.select();
            }
        }
    });

    if (globalSearchInput) {
        globalSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = globalSearchInput.value.trim();
                if (query) {
                    window.location.href = `/admin/api/item/?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }

    // ─── 3. Dashboard Live Table Filtering ────────────────────────────────────
    const filterCategory = document.getElementById('filter-category');
    const filterStatus = document.getElementById('filter-status');
    const filterSearch = document.getElementById('filter-table-search');
    const tableRows = document.querySelectorAll('.dashboard-table-row');

    function applyDashboardFilters() {
        if (!tableRows.length) return;

        const catVal = filterCategory ? filterCategory.value.toLowerCase() : '';
        const statVal = filterStatus ? filterStatus.value.toLowerCase() : '';
        const searchVal = filterSearch ? filterSearch.value.toLowerCase().trim() : '';

        tableRows.forEach(row => {
            const rowCat = (row.getAttribute('data-category') || '').toLowerCase();
            const rowStat = (row.getAttribute('data-status') || '').toLowerCase();
            const rowText = row.innerText.toLowerCase();

            let matchesCat = !catVal || rowCat === catVal;
            let matchesStat = !statVal || rowStat === statVal;
            let matchesSearch = !searchVal || rowText.includes(searchVal);

            if (matchesCat && matchesStat && matchesSearch) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    if (filterCategory) filterCategory.addEventListener('change', applyDashboardFilters);
    if (filterStatus) filterStatus.addEventListener('change', applyDashboardFilters);
    if (filterSearch) filterSearch.addEventListener('input', applyDashboardFilters);
});
