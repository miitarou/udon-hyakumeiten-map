/**
 * うどん百名店 2024 MAP - メインアプリケーション
 * Leaflet.js + MarkerCluster による地図ビジュアライゼーション
 */

(function () {
    'use strict';

    // === State ===
    let allRestaurants = [];
    let filteredRestaurants = [];
    let map = null;
    let markerClusterGroup = null;
    let markers = new Map(); // url -> marker
    let activeRegion = 'all';
    let activePrefecture = 'all';
    let firstSelectedOnly = false;
    let searchQuery = '';

    // === Map Tiles (CartoDB Voyager - ダークUIにも合う明るめタイル) ===
    const TILE_URL = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
    const TILE_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>';

    // === Japan Center ===
    const JAPAN_CENTER = [36.0, 137.0];
    const JAPAN_ZOOM = 6;

    // === Init ===
    async function init() {
        initMap();
        await loadData();
        populateFilters();
        applyFilters();
        bindEvents();
        updateStats();
        
        // パネルを初期表示（デスクトップ時）
        if (window.innerWidth > 768) {
            togglePanel(true);
        }
    }

    // === Map Initialization ===
    function initMap() {
        map = L.map('map', {
            center: JAPAN_CENTER,
            zoom: JAPAN_ZOOM,
            zoomControl: true,
            attributionControl: true,
            maxBounds: [[20, 120], [50, 155]],
            minZoom: 5,
            maxZoom: 18
        });

        L.tileLayer(TILE_URL, {
            attribution: TILE_ATTR,
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(map);

        markerClusterGroup = L.markerClusterGroup({
            maxClusterRadius: 50,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            zoomToBoundsOnClick: true,
            disableClusteringAtZoom: 15
        });

        map.addLayer(markerClusterGroup);
    }

    // === Data Loading ===
    async function loadData() {
        try {
            const response = await fetch('data/restaurants.json');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            allRestaurants = await response.json();
            console.log(`📊 データ読込完了: ${allRestaurants.length} 店舗`);
        } catch (e) {
            console.error('❌ データ読込失敗:', e);
            allRestaurants = [];
        }
    }

    // === Create Marker ===
    function createMarker(restaurant) {
        if (!restaurant.lat || !restaurant.lng) return null;

        const regionClass = restaurant.region.toLowerCase();
        const closedClass = restaurant.closed ? ' closed' : '';

        const icon = L.divIcon({
            className: 'custom-marker',
            html: `<div class="marker-pin ${regionClass}${closedClass}"></div>`,
            iconSize: [28, 36],
            iconAnchor: [14, 36],
            popupAnchor: [0, -36]
        });

        const marker = L.marker([restaurant.lat, restaurant.lng], { icon });

        // ポップアップ
        const popupContent = buildPopupContent(restaurant);
        marker.bindPopup(popupContent, {
            maxWidth: 300,
            minWidth: 280,
            closeButton: true,
            autoPan: true
        });

        return marker;
    }

    // === Build Popup Content ===
    function buildPopupContent(r) {
        const regionClass = r.region.toLowerCase();
        
        let closedBanner = '';
        if (r.closed) {
            closedBanner = `
                <div class="popup-closed-banner">
                    <span class="popup-closed-text">⚠ この店舗は閉店しました</span>
                </div>`;
        }

        let badges = '';
        if (r.firstSelected) {
            badges += '<span class="badge badge-new">初選出</span>';
        }
        if (r.closed) {
            badges += '<span class="badge badge-closed">閉店</span>';
        }
        const badgesHtml = badges ? `<div class="popup-badges">${badges}</div>` : '';

        return `
            <div class="popup-inner">
                <div class="popup-header">
                    <span class="popup-region-badge ${regionClass}">${r.region}</span>
                    <span class="popup-name">${escapeHtml(r.name)}</span>
                </div>
                ${closedBanner}
                <div class="popup-details">
                    <div class="popup-detail-row">
                        <span class="popup-detail-icon">📍</span>
                        <span class="popup-detail-text">${escapeHtml(r.prefecture)} ${escapeHtml(r.area)}</span>
                    </div>
                    ${r.holiday ? `
                    <div class="popup-detail-row">
                        <span class="popup-detail-icon">🗓</span>
                        <span class="popup-detail-text">${escapeHtml(r.holiday)}</span>
                    </div>` : ''}
                </div>
                ${badgesHtml}
                <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer" class="popup-link">
                    🔗 食べログで見る
                </a>
            </div>`;
    }

    // === Filters ===
    function populateFilters() {
        const prefSet = new Set();
        allRestaurants.forEach(r => prefSet.add(r.prefecture));
        
        const sortedPrefs = [...prefSet].sort();
        const select = document.getElementById('pref-select');
        
        sortedPrefs.forEach(pref => {
            const count = allRestaurants.filter(r => r.prefecture === pref).length;
            const option = document.createElement('option');
            option.value = pref;
            option.textContent = `${pref} (${count})`;
            select.appendChild(option);
        });
    }

    function applyFilters() {
        filteredRestaurants = allRestaurants.filter(r => {
            // Region filter
            if (activeRegion !== 'all' && r.region !== activeRegion) return false;
            
            // Prefecture filter
            if (activePrefecture !== 'all' && r.prefecture !== activePrefecture) return false;
            
            // First selected filter
            if (firstSelectedOnly && !r.firstSelected) return false;
            
            // Search filter
            if (searchQuery) {
                const q = searchQuery.toLowerCase();
                const searchTarget = `${r.name} ${r.prefecture} ${r.area} ${r.holiday}`.toLowerCase();
                if (!searchTarget.includes(q)) return false;
            }
            
            return true;
        });

        renderMarkers();
        renderList();
        updateVisibleCount();
    }

    // === Render Markers ===
    function renderMarkers() {
        markerClusterGroup.clearLayers();
        markers.clear();

        filteredRestaurants.forEach(r => {
            const marker = createMarker(r);
            if (marker) {
                markers.set(r.url, marker);
                markerClusterGroup.addLayer(marker);
            }
        });

        // フィルタ適用時にビューをフィット
        if (filteredRestaurants.length > 0 && filteredRestaurants.length < allRestaurants.length) {
            const validPoints = filteredRestaurants
                .filter(r => r.lat && r.lng)
                .map(r => [r.lat, r.lng]);
            
            if (validPoints.length > 0) {
                const bounds = L.latLngBounds(validPoints);
                map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
            }
        }
    }

    // === Render Restaurant List ===
    function renderList() {
        const container = document.getElementById('restaurant-list');
        container.innerHTML = '';

        filteredRestaurants.forEach((r, i) => {
            const card = document.createElement('div');
            card.className = 'restaurant-card';
            card.style.animationDelay = `${Math.min(i * 0.02, 0.5)}s`;
            
            let badgesHtml = '';
            if (r.firstSelected) badgesHtml += '<span class="badge badge-new">NEW</span>';
            if (r.closed) badgesHtml += '<span class="badge badge-closed">閉店</span>';

            card.innerHTML = `
                <div class="card-region-dot ${r.region.toLowerCase()}"></div>
                <div class="card-info">
                    <div class="card-name">${escapeHtml(r.name)}</div>
                    <div class="card-area">${escapeHtml(r.prefecture)} ${escapeHtml(r.area)}</div>
                </div>
                <div class="card-badges">${badgesHtml}</div>
            `;

            card.addEventListener('click', () => {
                focusRestaurant(r);
                // Active状態の更新
                container.querySelectorAll('.restaurant-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
            });

            container.appendChild(card);
        });
    }

    // === Focus on Restaurant ===
    function focusRestaurant(r) {
        if (!r.lat || !r.lng) return;

        map.setView([r.lat, r.lng], 16, { animate: true });

        const marker = markers.get(r.url);
        if (marker) {
            // クラスターからスパイダーフィを展開
            markerClusterGroup.zoomToShowLayer(marker, () => {
                marker.openPopup();
            });
        }

        // モバイルではパネルを閉じる
        if (window.innerWidth <= 768) {
            togglePanel(false);
        }
    }

    // === UI Updates ===
    function updateStats() {
        const total = allRestaurants.length;
        const east = allRestaurants.filter(r => r.region === 'EAST').length;
        const west = allRestaurants.filter(r => r.region === 'WEST').length;

        animateNumber('stat-total', total);
        animateNumber('stat-east', east);
        animateNumber('stat-west', west);
    }

    function animateNumber(elementId, target) {
        const el = document.getElementById(elementId);
        const duration = 800;
        const start = performance.now();
        const startVal = 0;

        function tick(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
            const current = Math.round(startVal + (target - startVal) * eased);
            el.textContent = current;
            if (progress < 1) requestAnimationFrame(tick);
        }

        requestAnimationFrame(tick);
    }

    function updateVisibleCount() {
        document.getElementById('visible-count').textContent = filteredRestaurants.length;
    }

    // === Panel Toggle ===
    function togglePanel(forceOpen) {
        const panel = document.getElementById('control-panel');
        const isOpen = panel.classList.contains('panel-open');
        
        if (forceOpen === true || (!isOpen && forceOpen !== false)) {
            panel.classList.remove('panel-closed');
            panel.classList.add('panel-open');
        } else {
            panel.classList.remove('panel-open');
            panel.classList.add('panel-closed');
        }
        
        // 地図のリサイズ
        setTimeout(() => map.invalidateSize(), 350);
    }

    // === Event Binding ===
    function bindEvents() {
        // Panel toggle
        document.getElementById('panel-toggle').addEventListener('click', () => togglePanel());

        // Region filter
        document.querySelectorAll('.region-filters .filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.region-filters .filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                activeRegion = btn.dataset.filter;
                applyFilters();
            });
        });

        // Prefecture filter
        document.getElementById('pref-select').addEventListener('change', (e) => {
            activePrefecture = e.target.value;
            applyFilters();
        });

        // First selected filter
        document.getElementById('first-selected-btn').addEventListener('click', () => {
            firstSelectedOnly = !firstSelectedOnly;
            document.getElementById('first-selected-btn').classList.toggle('active', firstSelectedOnly);
            applyFilters();
        });

        // Search
        let searchTimeout;
        document.getElementById('search-input').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchQuery = e.target.value.trim();
                applyFilters();
            }, 300);
        });

        // キーボードショートカット
        document.addEventListener('keydown', (e) => {
            // Escape: パネルを閉じる
            if (e.key === 'Escape') {
                togglePanel(false);
            }
            // Ctrl+K: 検索にフォーカス
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                togglePanel(true);
                document.getElementById('search-input').focus();
            }
        });
    }

    // === Utility ===
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // === Start ===
    document.addEventListener('DOMContentLoaded', init);

})();
