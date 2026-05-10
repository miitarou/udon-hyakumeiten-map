/**
 * うどん・そば百名店 MAP - メインアプリケーション
 * Leaflet.js + MarkerCluster による地図ビジュアライゼーション
 * うどん: 2017〜2024 / そば: 2017〜2025 全年度統合版
 */

(function () {
    'use strict';

    // === State ===
    let allRestaurants = [];   // udon + soba merged
    let allUdon = [];
    let allSoba = [];
    let filteredRestaurants = [];
    let visibleRestaurants = [];
    let udonHallOfFameThreshold = Infinity;
    let sobaHallOfFameThreshold = Infinity;
    let map = null;
    let markerClusterGroup = null;
    let markers = new Map();       // url -> marker
    let activeCategory = 'all';    // 'all' | 'udon' | 'soba'
    let activeRegion = 'all';
    let activePrefecture = 'all';
    let activeYear = 'all';
    let countFilterMode = 'all';  // 'all' | 'first' | 'exact-1' | 'min-N' | 'hall-of-fame'
    let activeStatus = 'all';     // 'all' | 'open' | 'closed'
    let saveFilter = 'all';       // 'all' | 'want' | 'visited' | 'none'
    let searchQuery = '';
    let sortMode = 'name';
    let distanceOrigin = null;    // { type: 'current' | 'picked', lat, lng, label, accuracy? }
    let searchDistanceOrigin = null; // { type: 'search', lat, lng, label }
    let searchDistanceSortActive = false;
    let radiusKm = 5;
    let radiusPickMode = false;
    let radiusMarker = null;
    let radiusCircle = null;
    let savedStates = {};
    let fitBoundsTimer = null;
    let tileErrorCount = 0;
    let swRefreshPending = false;
    const numberAnimationState = new Map();
    const SAVE_STORAGE_KEY = 'hyakumeiten-map-store-states-v1';
    const SAVE_BACKUP_FORMAT = 'udon-hyakumeiten-map.saved-states';
    const SAVE_BACKUP_VERSION = 1;
    const COMMON_SEARCH_REPLACEMENTS = [
        ['饂飩', 'うどん'],
        ['齊', '斉'],
        ['齋', '斉'],
        ['斎', '斉'],
        ['邊', '辺'],
        ['邉', '辺'],
        ['廣', '広'],
        ['國', '国'],
        ['櫻', '桜'],
        ['萬', '万'],
        ['壽', '寿'],
        ['藪', '薮']
    ];

    // === Map Tiles (国土地理院 淡色地図) ===
    const TILE_URL = 'https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png';
    const TILE_ATTR = '<a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>';

    const JAPAN_CENTER = [36.0, 137.0];
    const JAPAN_ZOOM = 6;

    // カテゴリごとの年度一覧
    const UDON_YEARS = [2017, 2018, 2019, 2020, 2022, 2024];
    const SOBA_YEARS = [2017, 2018, 2019, 2021, 2022, 2024, 2025];

    // === SVG アイコン定義 ===
    // うどん丼
    const UDON_SVG = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' width='28' height='28'>
        <path d='M15 45 C15 45 18 30 50 30 C82 30 85 45 85 45 L80 48 C80 48 75 36 50 36 C25 36 20 48 20 48 Z' fill='#D4A853'/>
        <path d='M20 48 C20 48 22 75 50 80 C78 75 80 48 80 48 Z' fill='#D4A853'/>
        <path d='M35 42 Q50 32 65 42' stroke='#E8C547' stroke-width='3' fill='none' stroke-linecap='round'/>
        <path d='M30 48 Q45 38 60 48' stroke='#E8C547' stroke-width='3' fill='none' stroke-linecap='round'/>
        <path d='M40 36 Q55 26 70 36' stroke='#E8C547' stroke-width='3' fill='none' stroke-linecap='round'/>
        <path d='M42 80 L38 95 L62 95 L58 80' fill='#D4A853'/>
    </svg>`;

    // そば猪口
    const SOBA_SVG = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' width='28' height='28'>
        <path d='M12 42 L88 42 L73 82 L27 82 Z' fill='#7B9E6B'/>
        <path d='M10 42 L90 42' stroke='#9DBF8A' stroke-width='6' stroke-linecap='round'/>
        <path d='M20 30 Q35 20 50 26 Q65 32 80 22' stroke='#9DBF8A' stroke-width='3.5' fill='none' stroke-linecap='round'/>
        <path d='M22 38 Q37 28 52 34 Q67 40 82 30' stroke='#9DBF8A' stroke-width='3' fill='none' stroke-linecap='round'/>
        <path d='M27 82 L23 95 L77 95 L73 82 Z' fill='#7B9E6B'/>
    </svg>`;

    // === Init ===
    async function init() {
        console.log('🚀 初期化開始');
        try {
            initMap();
            loadSavedStates();
            await loadData();
            rebuildYearButtons();
            populateFilters();
            applyFilters();
            bindEvents();
            updateStats();
            updateLogoForCategory();
            hideLoadingOverlay();
            registerServiceWorker();

            if (window.innerWidth > 768) {
                togglePanel(true);
            }
            console.log('✅ 初期化完了');
        } catch (e) {
            console.error('❌ 初期化エラー:', e);
            showLoadingError('データまたは地図ライブラリの読み込みに失敗しました。時間をおいて再読み込みしてください。');
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

        const baseLayer = L.tileLayer(TILE_URL, {
            attribution: TILE_ATTR,
            maxZoom: 18
        });
        baseLayer.on('tileerror', () => {
            tileErrorCount += 1;
            if (tileErrorCount >= 3) {
                showOfflineBanner('地図タイルを読み込めません。通信状態を確認してください。店舗リストと保存情報は利用できます。');
            }
        });
        baseLayer.on('tileload', () => {
            if (tileErrorCount > 0) tileErrorCount -= 1;
            if (navigator.onLine && tileErrorCount === 0) hideOfflineBanner();
        });
        baseLayer.addTo(map);

        markerClusterGroup = L.markerClusterGroup({
            maxClusterRadius: 50,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            zoomToBoundsOnClick: true,
            disableClusteringAtZoom: 15
        });

        map.addLayer(markerClusterGroup);
        map.on('click', handleMapClick);
        map.on('moveend zoomend', updateMapViewportState);
    }

    // === Data Loading ===
    async function loadData() {
        const fetchJson = async (url) => {
            try {
                const res = await fetch(url);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return await res.json();
            } catch {
                return await loadDataXHR(url);
            }
        };

        const udonRaw = await fetchJson('data/udon.json');
        const sobaRaw = await fetchJson('data/soba.json');
        if (!Array.isArray(udonRaw) || !Array.isArray(sobaRaw)) {
            throw new Error('Restaurant data should be JSON arrays');
        }

        // category フィールドと years の正規化
        udonRaw.forEach(r => {
            r.category = 'udon';
            if (!r.years || !Array.isArray(r.years)) r.years = [2024];
        });
        sobaRaw.forEach(r => {
            r.category = 'soba';
            if (!r.years || !Array.isArray(r.years)) r.years = [2025];
        });

        allUdon = udonRaw;
        allSoba = sobaRaw;
        allRestaurants = [...udonRaw, ...sobaRaw];

        function calcThreshold(src) {
            const counts = src.map(r => r.years ? r.years.length : 0).filter(c => c > 0).sort((a, b) => b - a);
            if (!counts.length) return Infinity;
            return counts[Math.max(0, Math.ceil(counts.length * 0.1) - 1)];
        }
        udonHallOfFameThreshold = calcThreshold(allUdon);
        sobaHallOfFameThreshold = calcThreshold(allSoba);

        console.log(`📊 データ読込完了: うどん ${allUdon.length} 店 (殿堂閾値:${udonHallOfFameThreshold}) / そば ${allSoba.length} 店 (殿堂閾値:${sobaHallOfFameThreshold})`);
    }

    function loadDataXHR(url) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.onload = function () {
                if (xhr.status === 200 || xhr.status === 0) {
                    try { resolve(JSON.parse(xhr.responseText)); }
                    catch (e) { reject(e); }
                } else {
                    reject(new Error(`XHR ${xhr.status}`));
                }
            };
            xhr.onerror = () => reject(new Error('XHR error'));
            xhr.send();
        });
    }

    // === 年度ボタンを動的生成 ===
    function getAvailableYears() {
        if (activeCategory === 'udon') return UDON_YEARS;
        if (activeCategory === 'soba') return SOBA_YEARS;
        // ALL: 両方の union, 降順
        const set = new Set([...UDON_YEARS, ...SOBA_YEARS]);
        return [...set].sort((a, b) => b - a);
    }

    function rebuildYearButtons() {
        const container = document.getElementById('year-filters');
        if (!container) return;

        const years = getAvailableYears();
        // 現在の activeYear が新しいリストに含まれていなければリセット
        if (activeYear !== 'all' && !years.includes(parseInt(activeYear, 10))) {
            activeYear = 'all';
        }

        container.innerHTML = '';

        const allBtn = document.createElement('button');
        allBtn.className = 'filter-btn' + (activeYear === 'all' ? ' active' : '');
        allBtn.dataset.year = 'all';
        allBtn.setAttribute('aria-pressed', activeYear === 'all' ? 'true' : 'false');
        allBtn.textContent = '全年度';
        container.appendChild(allBtn);

        [...years].sort((a, b) => b - a).forEach(y => {
            const btn = document.createElement('button');
            const ys = String(y);
            btn.className = 'filter-btn year-filter-btn' + (activeYear === ys ? ' active' : '');
            btn.dataset.year = ys;
            btn.setAttribute('aria-pressed', activeYear === ys ? 'true' : 'false');
            btn.textContent = ys;
            container.appendChild(btn);
        });

        bindYearFilterEvents();
    }

    function bindYearFilterEvents() {
        const container = document.getElementById('year-filters');
        if (!container) return;
        container.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                container.querySelectorAll('.filter-btn').forEach(b => {
                    b.classList.remove('active');
                    b.setAttribute('aria-pressed', 'false');
                });
                this.classList.add('active');
                this.setAttribute('aria-pressed', 'true');
                activeYear = this.dataset.year;
                applyFilters();
            });
        });
    }

    // === ロゴアイコン・タイトルをカテゴリに合わせて更新 ===
    function updateLogoForCategory() {
        const logoIcon = document.getElementById('logo-icon');
        const logoTitle = document.getElementById('logo-title');
        const logoSubtitle = document.getElementById('logo-subtitle');
        const titleBadge = document.getElementById('title-badge');

        if (activeCategory === 'udon') {
            if (logoIcon) logoIcon.innerHTML = UDON_SVG;
            if (logoTitle) logoTitle.innerHTML = 'うどん百名店 <span class="header-year-badge" id="title-badge">2017-2024</span>';
            if (logoSubtitle) logoSubtitle.textContent = 'EAST × WEST × KAGAWA MAP';
        } else if (activeCategory === 'soba') {
            if (logoIcon) logoIcon.innerHTML = SOBA_SVG;
            if (logoTitle) logoTitle.innerHTML = 'そば百名店 <span class="header-year-badge soba-badge" id="title-badge">2017-2025</span>';
            if (logoSubtitle) logoSubtitle.textContent = 'EAST × WEST MAP';
        } else {
            // ALL
            if (logoIcon) {
                logoIcon.innerHTML = `
                    <span style="display:inline-flex;gap:2px">
                        ${UDON_SVG.replace('width=\'28\'', 'width=\'22\'').replace('height=\'28\'', 'height=\'22\'')}
                        ${SOBA_SVG.replace('width=\'28\'', 'width=\'22\'').replace('height=\'28\'', 'height=\'22\'')}
                    </span>`;
            }
            if (logoTitle) logoTitle.innerHTML = '百名店 <span class="header-year-badge" id="title-badge">2017-2025</span>';
            if (logoSubtitle) logoSubtitle.textContent = 'うどん・そば MAP';
        }
    }

    // === Create Marker ===
    function createMarker(restaurant) {
        if (!restaurant.lat || !restaurant.lng) return null;

        const regionClass = toCssClass(restaurant.region);
        const categoryClass = restaurant.category === 'soba' ? ' soba' : '';
        const closedClass = restaurant.closed ? ' closed' : '';
        const selectCount = restaurant.years ? restaurant.years.length : 0;

        let selectClass = '';
        let markerSize = [28, 36];
        let anchorPos = [14, 36];
        
        const hofThreshold = restaurant.category === 'soba' ? sobaHallOfFameThreshold : udonHallOfFameThreshold;
        
        if (selectCount >= hofThreshold) {
            selectClass = ' select-high';
            markerSize = [36, 44];
            anchorPos = [18, 44];
        } else if (selectCount >= Math.max(2, hofThreshold - 2)) {
            selectClass = ' select-mid';
            markerSize = [32, 40];
            anchorPos = [16, 40];
        }

        const icon = L.divIcon({
            className: 'custom-marker',
            html: `<div class="marker-pin ${regionClass}${categoryClass}${closedClass}${selectClass}">
                     <span class="marker-count">${selectCount}</span>
                   </div>`,
            iconSize: markerSize,
            iconAnchor: anchorPos,
            popupAnchor: [0, -anchorPos[1]]
        });

        const marker = L.marker([restaurant.lat, restaurant.lng], { icon });

        const popupContent = buildPopupContent(restaurant);
        marker.bindPopup(popupContent, {
            maxWidth: 300,
            minWidth: 280,
            closeButton: true,
            autoPan: true
        });

        const labelClass = 'marker-label' + (restaurant.closed ? ' marker-label-closed' : '');
        const tooltip = document.createElement('span');
        tooltip.textContent = restaurant.name || '';
        marker.bindTooltip(tooltip, {
            permanent: true,
            direction: 'right',
            offset: [12, -10],
            className: labelClass,
            opacity: 0.95
        });

        return marker;
    }

    // === Build Year Badges ===
    function buildYearBadges(years) {
        if (!years || years.length === 0) return '';
        return years.map(y => {
            const shortYear = String(y).slice(2);
            return `<span class="year-badge year-${y}">'${shortYear}</span>`;
        }).join('');
    }

    // === Build Popup Content ===
    function buildPopupContent(r) {
        // All restaurant-data-derived text inserted via innerHTML must be escaped.
        const regionClass = toCssClass(r.region);
        const selectCount = r.years ? r.years.length : 0;
        const isSoba = r.category === 'soba';

        let closedBanner = '';
        if (r.closed) {
            closedBanner = `<div class="popup-closed-banner"><span class="popup-closed-text">⚠ この店舗は閉店しました</span></div>`;
        }

        let badges = '';
        if (r.firstSelected) badges += '<span class="badge badge-new">初選出</span>';
        if (r.closed) badges += '<span class="badge badge-closed">閉店</span>';
        if (isSoba) badges += '<span class="badge badge-soba">🥢 そば</span>';
        const badgesHtml = badges ? `<div class="popup-badges">${badges}</div>` : '';

        const yearBadgesHtml = buildYearBadges(r.years);
        const countText = selectCount > 0 ? `<span class="popup-select-count${isSoba ? ' soba-count' : ''}">${selectCount}回選出</span>` : '';

        const distanceOrigin = getActiveDistanceOrigin();
        const distText = (distanceOrigin && r.lat != null) ?
            `<div class="popup-detail-row"><span class="popup-detail-icon">📏</span><span class="popup-detail-text">${distanceOrigin.label}から ${formatDistance(calcDistance(distanceOrigin.lat, distanceOrigin.lng, r.lat, r.lng))}</span></div>` : '';

        const mapLinksHtml = (r.lat != null && r.lng != null) ? `
            <div class="popup-map-links">
                <a href="${getGoogleMapsSearchUrl(r)}" target="_blank" rel="noopener noreferrer" class="popup-map-btn popup-map-google">
                    🗺 Googleで見る
                </a>
            </div>` : '';

        const linkClass = isSoba ? 'popup-link soba-link' : 'popup-link';

        return `
            <div class="popup-inner">
                <div class="popup-header">
                    <span class="popup-region-badge ${regionClass}">${escapeHtml(r.region)}</span>
                    <div class="popup-title-area">
                        <span class="popup-name">${escapeHtml(r.name)}</span>
                        ${countText}
                    </div>
                </div>
                <div class="popup-year-badges">${yearBadgesHtml}</div>
                ${closedBanner}
                <div class="popup-details">
                    <div class="popup-detail-row">
                        <span class="popup-detail-icon">📍</span>
                        <span class="popup-detail-text">${escapeHtml(r.prefecture)} ${escapeHtml(r.area)}</span>
                    </div>
                    ${r.holiday ? `<div class="popup-detail-row"><span class="popup-detail-icon">🗓</span><span class="popup-detail-text">${escapeHtml(r.holiday)}</span></div>` : ''}
                    ${distText}
                </div>
                ${badgesHtml}
                ${isSafeUrl(r.url) ? `<a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer" class="${linkClass}">` : `<span class="${linkClass} popup-link-disabled">`}
                    🔗 食べログで見る
                ${isSafeUrl(r.url) ? '</a>' : '</span>'}
                ${mapLinksHtml}
                ${buildSaveButtons(r, 'popup-save-actions')}
            </div>`;
    }

    // === Filters ===
    function populateFilters() {
        const src = getCategorySource();
        const prefSet = new Set();
        src.forEach(r => { if (r.prefecture) prefSet.add(r.prefecture); });

        const sortedPrefs = [...prefSet].sort();
        const select = document.getElementById('pref-select');
        if (!select) return;

        // 既存オプションを削除（「すべて」は残す）
        while (select.options.length > 1) select.remove(1);

        sortedPrefs.forEach(pref => {
            const count = src.filter(r => r.prefecture === pref).length;
            const option = document.createElement('option');
            option.value = pref;
            option.textContent = `${pref} (${count})`;
            select.appendChild(option);
        });

        // 現在の選択が新リストにない場合はリセット
        if (activePrefecture !== 'all' && !prefSet.has(activePrefecture)) {
            activePrefecture = 'all';
            select.value = 'all';
        }
    }

    function getCategorySource() {
        if (activeCategory === 'udon') return allUdon;
        if (activeCategory === 'soba') return allSoba;
        return allRestaurants;
    }

    function getCountFilterBase(src) {
        return src.filter(r => {
            if (activeRegion !== 'all' && r.region !== activeRegion) return false;
            if (activePrefecture !== 'all' && r.prefecture !== activePrefecture) return false;
            if (activeYear !== 'all') {
                const yearNum = parseInt(activeYear, 10);
                if (!r.years || !r.years.includes(yearNum)) return false;
            }
            return true;
        });
    }

    function getHallOfFameThreshold(src) {
        if (src === allUdon) return udonHallOfFameThreshold;
        if (src === allSoba) return sobaHallOfFameThreshold;
        // fallback for ALL
        return Math.min(udonHallOfFameThreshold, sobaHallOfFameThreshold);
    }

    function matchesCountFilter(r, src) {
        const count = r.years ? r.years.length : 0;
        if (countFilterMode === 'all') return true;
        if (countFilterMode === 'first') return Boolean(r.firstSelected);
        if (countFilterMode === 'exact-1') return count === 1;
        if (countFilterMode === 'hall-of-fame') return count >= getHallOfFameThreshold(src);
        if (countFilterMode.startsWith('min-')) {
            const min = parseInt(countFilterMode.replace('min-', ''), 10) || 0;
            return count >= min;
        }
        return true;
    }

    function applyFilters() {
        const src = getCategorySource();

        filteredRestaurants = src.filter(r => {
            // Region
            if (activeRegion !== 'all' && r.region !== activeRegion) return false;
            // Prefecture
            if (activePrefecture !== 'all' && r.prefecture !== activePrefecture) return false;
            // Year
            if (activeYear !== 'all') {
                const yearNum = parseInt(activeYear, 10);
                if (!r.years || !r.years.includes(yearNum)) return false;
            }
            // Selection count
            if (!matchesCountFilter(r, src)) return false;
            // Business status
            if (activeStatus === 'open' && r.closed) return false;
            if (activeStatus === 'closed' && !r.closed) return false;
            // Saved state
            const currentSavedState = getSavedState(r);
            if (saveFilter === 'want' && currentSavedState !== 'want') return false;
            if (saveFilter === 'visited' && currentSavedState !== 'visited') return false;
            if (saveFilter === 'none' && currentSavedState !== 'none') return false;
            // Distance radius search
            if (distanceOrigin && radiusKm !== 'none') {
                const d = calcDistance(distanceOrigin.lat, distanceOrigin.lng, r.lat, r.lng);
                if (d > radiusKm) return false;
            }
            // Search by store name, address, nearest station/area, prefecture, and holiday.
            if (searchQuery) {
                const queries = buildSearchQueries(searchQuery);
                if (!isSearchMatch(r, queries)) return false;
            }
            return true;
        });

        updateSearchDistanceOrigin();
        sortRestaurants();
        renderMarkers();
        updateMapViewportState();
        syncDistanceSortControl();
    }

    // === Sort ===
    function sortRestaurants() {
        if (searchDistanceSortActive && searchDistanceOrigin && !distanceOrigin) {
            sortByDistance(searchDistanceOrigin);
            return;
        }

        switch (sortMode) {
            case 'name':
                filteredRestaurants.sort((a, b) => (a.name || '').localeCompare(b.name || '', 'ja'));
                break;
            case 'count-desc':
                filteredRestaurants.sort((a, b) => {
                    const ca = a.years ? a.years.length : 0;
                    const cb = b.years ? b.years.length : 0;
                    return cb - ca || (a.name || '').localeCompare(b.name || '', 'ja');
                });
                break;
            case 'count-asc':
                filteredRestaurants.sort((a, b) => {
                    const ca = a.years ? a.years.length : 0;
                    const cb = b.years ? b.years.length : 0;
                    return ca - cb || (a.name || '').localeCompare(b.name || '', 'ja');
                });
                break;
            case 'pref':
                filteredRestaurants.sort((a, b) =>
                    (a.prefecture || '').localeCompare(b.prefecture || '', 'ja') ||
                    (a.name || '').localeCompare(b.name || '', 'ja')
                );
                break;
            case 'distance':
                {
                    const origin = getActiveDistanceOrigin();
                    if (!origin) break;
                    sortByDistance(origin);
                }
                break;
        }
    }

    function sortByDistance(origin) {
        filteredRestaurants.sort((a, b) => {
            const da = calcDistance(origin.lat, origin.lng, a.lat, a.lng);
            const db = calcDistance(origin.lat, origin.lng, b.lat, b.lng);
            return da - db;
        });
    }

    // === Haversine 距離計算 (km) ===
    function calcDistance(lat1, lon1, lat2, lon2) {
        if (lat2 == null || lon2 == null) return Infinity;
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    function formatDistance(km) {
        if (km === Infinity || km == null) return '';
        if (km < 1) return Math.round(km * 1000) + 'm';
        if (km < 10) return km.toFixed(1) + 'km';
        return Math.round(km) + 'km';
    }

    function getGoogleMapsSearchUrl(r) {
        const query = `${r.name || ''} ${r.lat},${r.lng}`.trim();
        return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
    }

    function getActiveDistanceOrigin() {
        return distanceOrigin || searchDistanceOrigin;
    }

    function normalizeSearchText(value) {
        let text = String(value || '')
            .normalize('NFKC')
            .toLowerCase();
        COMMON_SEARCH_REPLACEMENTS.forEach(([from, to]) => {
            text = text.replaceAll(from, to);
        });
        return toHiragana(text)
            .replace(/[‐‑‒–—―ー−]/g, '-')
            .replace(/\s+/g, '');
    }

    function toHiragana(value) {
        return String(value || '').replace(/[\u30a1-\u30f6]/g, ch =>
            String.fromCharCode(ch.charCodeAt(0) - 0x60)
        );
    }

    function buildSearchQueries(query) {
        const normalized = normalizeSearchText(query);
        const base = normalized.replace(/[市区町村駅]$/g, '');
        return [...new Set([normalized, base].filter(Boolean))];
    }

    function buildSearchTarget(r) {
        const area = r.area || '';
        const areaBase = area.replace(/駅$/, '').replace(/（.+?）/g, '');
        return normalizeSearchText([
            r.name,
            r.prefecture,
            area,
            areaBase,
            r.address,
            r.holiday
        ].filter(Boolean).join(' '));
    }

    function buildSearchTokens(r) {
        const area = r.area || '';
        const areaBase = area.replace(/駅$/, '').replace(/（.+?）/g, '');
        return [...new Set([
            r.name,
            r.prefecture,
            area,
            areaBase,
            r.address,
            r.holiday
        ].filter(Boolean).flatMap(value =>
            String(value).split(/[\s　,、，・/／()（）「」『』【】\[\]-]+/)
        ).map(normalizeSearchText).filter(token => token.length >= 2))];
    }

    function buildLocationSearchTarget(r) {
        const area = r.area || '';
        const areaBase = area.replace(/駅$/, '').replace(/（.+?）/g, '');
        return normalizeSearchText([
            area,
            areaBase,
            r.address
        ].filter(Boolean).join(' '));
    }

    function isNameSearchMatch(r, queries) {
        const name = normalizeSearchText(r.name);
        return queries.some(q => name === q || name.includes(q));
    }

    function isLocationSearchMatch(r, queries) {
        const locationTarget = buildLocationSearchTarget(r);
        return queries.some(q => locationTarget.includes(q));
    }

    function isSearchMatch(r, queries) {
        const target = buildSearchTarget(r);
        if (queries.some(q => target.includes(q))) return true;

        const tokens = buildSearchTokens(r);
        return queries.some(q =>
            isFuzzyQuery(q) &&
            tokens.some(token => isNearSearchToken(q, token))
        );
    }

    function isFuzzyQuery(query) {
        return /^[\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}a-z0-9-]+$/u.test(query) && query.length >= 3;
    }

    function isNearSearchToken(query, token) {
        if (!query || !token) return false;
        if (token.includes(query) || query.includes(token)) return true;
        const maxDistance = query.length >= 7 ? 2 : 1;
        if (Math.abs(query.length - token.length) > maxDistance) return false;
        return editDistanceWithin(query, token, maxDistance);
    }

    function editDistanceWithin(a, b, maxDistance) {
        const costs = Array.from({ length: b.length + 1 }, (_, i) => i);
        for (let i = 1; i <= a.length; i++) {
            let diagonal = costs[0];
            costs[0] = i;
            let rowMin = costs[0];
            for (let j = 1; j <= b.length; j++) {
                const before = costs[j];
                costs[j] = Math.min(
                    costs[j] + 1,
                    costs[j - 1] + 1,
                    diagonal + (a[i - 1] === b[j - 1] ? 0 : 1)
                );
                diagonal = before;
                rowMin = Math.min(rowMin, costs[j]);
            }
            if (rowMin > maxDistance) return false;
        }
        return costs[b.length] <= maxDistance;
    }

    function updateSearchDistanceOrigin() {
        searchDistanceOrigin = null;
        searchDistanceSortActive = false;
        if (distanceOrigin || !searchQuery || filteredRestaurants.length < 2) return;

        const queries = buildSearchQueries(searchQuery);
        const nameMatches = filteredRestaurants.filter(r => isNameSearchMatch(r, queries));
        const exactNameMatches = filteredRestaurants.filter(r => {
            const name = normalizeSearchText(r.name);
            return queries.some(q => name === q);
        });
        const locationMatches = filteredRestaurants.filter(r =>
            r.lat != null &&
            r.lng != null &&
            isLocationSearchMatch(r, queries)
        );

        if (exactNameMatches.length > 0) return;
        if (locationMatches.length < 2) return;
        if (nameMatches.length > locationMatches.length) return;

        searchDistanceOrigin = {
            type: 'search',
            lat: locationMatches.reduce((sum, r) => sum + r.lat, 0) / locationMatches.length,
            lng: locationMatches.reduce((sum, r) => sum + r.lng, 0) / locationMatches.length,
            label: '検索結果'
        };
        searchDistanceSortActive = true;
    }

    // === Local Save State ===
    function loadSavedStates() {
        try {
            const raw = localStorage.getItem(SAVE_STORAGE_KEY);
            savedStates = raw ? JSON.parse(raw) : {};
        } catch {
            savedStates = {};
        }
    }

    function persistSavedStates() {
        localStorage.setItem(SAVE_STORAGE_KEY, JSON.stringify(savedStates));
    }

    function getSavedState(r) {
        return savedStates[r.url] || 'none';
    }

    function setSavedState(url, state) {
        if (state === 'none') delete savedStates[url];
        else savedStates[url] = state;
        persistSavedStates();
        applyFilters();
    }

    function buildSaveButtons(r, contextClass) {
        const state = getSavedState(r);
        const safeUrl = encodeURIComponent(r.url);
        return `
            <div class="${contextClass}">
                <button type="button" class="save-btn ${state === 'want' ? 'active' : ''}" data-save-url="${safeUrl}" data-save-state="want" aria-pressed="${state === 'want'}">行きたい</button>
                <button type="button" class="save-btn ${state === 'visited' ? 'active visited' : ''}" data-save-url="${safeUrl}" data-save-state="visited" aria-pressed="${state === 'visited'}">訪問済み</button>
            </div>`;
    }

    function handleSaveButtonClick(btn) {
        const url = decodeURIComponent(btn.dataset.saveUrl || '');
        const nextState = btn.dataset.saveState || 'none';
        if (!url) return;
        const current = savedStates[url] || 'none';
        setSavedState(url, current === nextState ? 'none' : nextState);
    }

    function getRestaurantByUrl(url) {
        return allRestaurants.find(r => r.url === url) || null;
    }

    function buildSavedStateEntry(url, state) {
        const r = getRestaurantByUrl(url);
        return {
            url,
            state,
            name: r?.name || null,
            category: r?.category || null,
            prefecture: r?.prefecture || null,
            area: r?.area || null,
            address: r?.address || null,
            current: Boolean(r)
        };
    }

    function exportSavedStates() {
        const entries = Object.entries(savedStates)
            .filter(([, state]) => state === 'want' || state === 'visited')
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([url, state]) => buildSavedStateEntry(url, state));

        const payload = {
            format: SAVE_BACKUP_FORMAT,
            version: SAVE_BACKUP_VERSION,
            exportedAt: new Date().toISOString(),
            source: location.href,
            total: entries.length,
            stores: entries
        };

        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const date = new Date().toISOString().slice(0, 10);
        const link = document.createElement('a');
        link.href = url;
        link.download = `hyakumeiten-saved-states-${date}.json`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }

    function normalizeImportedSaveEntries(data) {
        if (!data || typeof data !== 'object') throw new Error('JSONの形式を読み取れませんでした。');

        const source = Array.isArray(data.stores) ? data.stores
            : Array.isArray(data.items) ? data.items
                : Array.isArray(data.entries) ? data.entries
                    : null;

        if (source) {
            return source.map(item => ({
                url: item.url,
                state: item.state,
                name: item.name,
                category: item.category,
                prefecture: item.prefecture,
                area: item.area,
                address: item.address
            }));
        }

        const stateMap = data.savedStates && typeof data.savedStates === 'object' ? data.savedStates : data;
        return Object.entries(stateMap).map(([url, state]) => ({ url, state }));
    }

    function findRestaurantForImportedEntry(entry) {
        if (entry.url) {
            const byUrl = getRestaurantByUrl(entry.url);
            if (byUrl) return byUrl;
        }

        const name = normalizeSearchText(entry.name);
        const address = normalizeSearchText(entry.address);
        const category = normalizeSearchText(entry.category);
        const prefecture = normalizeSearchText(entry.prefecture);
        if (!name) return null;

        const exactAddressMatches = allRestaurants.filter(r =>
            normalizeSearchText(r.name) === name &&
            address &&
            normalizeSearchText(r.address) === address
        );
        if (exactAddressMatches.length === 1) return exactAddressMatches[0];

        const scopedNameMatches = allRestaurants.filter(r =>
            normalizeSearchText(r.name) === name &&
            (!category || normalizeSearchText(r.category) === category) &&
            (!prefecture || normalizeSearchText(r.prefecture) === prefecture)
        );
        if (scopedNameMatches.length === 1) return scopedNameMatches[0];

        return null;
    }

    function importSavedStates(data) {
        const entries = normalizeImportedSaveEntries(data);
        const nextStates = { ...savedStates };
        const stats = { imported: 0, remapped: 0, missing: [], skipped: 0 };

        entries.forEach(entry => {
            const state = entry.state;
            if (state !== 'want' && state !== 'visited' && state !== 'none') {
                stats.skipped += 1;
                return;
            }

            const matched = findRestaurantForImportedEntry(entry);
            if (!matched) {
                stats.missing.push({
                    name: entry.name || entry.url || '不明な店舗',
                    address: entry.address || entry.area || '',
                    state
                });
                return;
            }

            const targetUrl = matched.url;
            if (state === 'none') delete nextStates[targetUrl];
            else nextStates[targetUrl] = state;

            stats.imported += 1;
            if (matched && entry.url && matched.url !== entry.url) stats.remapped += 1;
        });

        savedStates = nextStates;
        persistSavedStates();
        applyFilters();
        return stats;
    }

    function handleImportFile(file) {
        const reader = new FileReader();
        reader.onload = () => {
            try {
                const stats = importSavedStates(JSON.parse(reader.result));
                alert([
                    `保存状態を復元しました。`,
                    `反映: ${stats.imported}件`,
                    stats.remapped ? `現行店舗へ再対応: ${stats.remapped}件` : null,
                    stats.missing.length ? `現行マップにない保存データ: ${stats.missing.length}件` : null,
                    stats.missing.length ? stats.missing.slice(0, 10).map(item =>
                        `- ${item.name}${item.address ? ` / ${item.address}` : ''} / ${item.state === 'want' ? '行きたい' : '訪問済み'}`
                    ).join('\n') : null,
                    stats.missing.length > 10 ? `ほか${stats.missing.length - 10}件` : null,
                    stats.skipped ? `スキップ: ${stats.skipped}件` : null
                ].filter(Boolean).join('\n'));
            } catch (e) {
                alert(`復元できませんでした。\n${e.message || e}`);
            }
        };
        reader.readAsText(file);
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

        if (filteredRestaurants.length > 0 && filteredRestaurants.length < allRestaurants.length) {
            const validPoints = filteredRestaurants
                .filter(r => r.lat && r.lng)
                .map(r => [r.lat, r.lng]);

            if (validPoints.length > 0) {
                clearTimeout(fitBoundsTimer);
                fitBoundsTimer = setTimeout(() => {
                    const bounds = L.latLngBounds(validPoints);
                    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
                }, 200);
            }
        }
    }

    // === Render Restaurant List ===
    function renderList() {
        const container = document.getElementById('restaurant-list');
        container.innerHTML = '';
        const listRestaurants = visibleRestaurants;

        if (filteredRestaurants.length === 0) {
            const emptyCat = activeCategory === 'soba' ? '🥢' : activeCategory === 'udon' ? '🍜' : '🍜';
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">${emptyCat}</div>
                    <div class="empty-state-title">該当する店舗が見つかりません</div>
                    <div class="empty-state-desc">検索条件を変更するか、フィルタをリセットしてください。</div>
                    <button class="empty-state-reset" id="empty-reset-btn">フィルタをリセット</button>
                </div>`;
            const resetBtn = document.getElementById('empty-reset-btn');
            if (resetBtn) resetBtn.addEventListener('click', resetAllFilters);
            return;
        }

        if (listRestaurants.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🗺</div>
                    <div class="empty-state-title">地図内に店舗がありません</div>
                    <div class="empty-state-desc">地図を移動または縮小すると、表示範囲内の店舗がリストに出ます。</div>
                </div>`;
            return;
        }

        listRestaurants.forEach((r, i) => {
            const card = document.createElement('div');
            card.className = 'restaurant-card';
            card.style.animationDelay = `${Math.min(i * 0.02, 0.5)}s`;

            const selectCount = r.years ? r.years.length : 0;
            const isSoba = r.category === 'soba';
            const savedState = getSavedState(r);

            let badgesHtml = '';
            if (r.firstSelected) badgesHtml += '<span class="badge badge-new">NEW</span>';
            if (r.closed) badgesHtml += '<span class="badge badge-closed">閉店</span>';

            const yearBadgesHtml = buildYearBadges(r.years);
            const hofThreshold = isSoba ? sobaHallOfFameThreshold : udonHallOfFameThreshold;
            const countBadgeClass = selectCount >= hofThreshold ? 'count-badge-gold' : selectCount >= Math.max(2, hofThreshold - 2) ? 'count-badge-silver' : '';
            const countBadge = `<span class="count-badge ${countBadgeClass}">${selectCount}回</span>`;

            const distanceOrigin = getActiveDistanceOrigin();
            const distStr = (distanceOrigin && r.lat != null) ?
                formatDistance(calcDistance(distanceOrigin.lat, distanceOrigin.lng, r.lat, r.lng)) : '';
            const distHtml = distStr ? `<span class="card-distance">📏 ${distStr}</span>` : '';

            const cardMapBtn = (r.lat != null && r.lng != null) ?
                `<div class="card-map-links">
                    <button type="button" class="card-map-btn card-focus-btn" data-focus-url="${encodeURIComponent(r.url)}" title="地図で表示" aria-label="${escapeHtml(r.name)}を地図で表示">📍</button>
                    <a href="${getGoogleMapsSearchUrl(r)}" target="_blank" rel="noopener noreferrer" class="card-map-btn" title="Googleで見る" aria-label="${escapeHtml(r.name)}をGoogleで見る" onclick="event.stopPropagation()">🗺</a>
                </div>` : '';

            // Security: all restaurant-data-derived text inserted via innerHTML must be escaped.
            // URL attributes must be validated or generated by trusted builders.
            const dotClass = isSoba
                ? `${toCssClass(r.region)} soba`
                : toCssClass(r.region);

            card.innerHTML = `
                <div class="card-region-dot ${dotClass}"></div>
                <div class="card-info">
                    <div class="card-name">${escapeHtml(r.name)}</div>
                    <div class="card-area">${escapeHtml(r.prefecture)} ${escapeHtml(r.area)} ${distHtml}</div>
                    <div class="card-badges-row">
                        ${countBadge}
                        <div class="card-year-badges">${yearBadgesHtml}</div>
                        ${badgesHtml}
                    </div>
                </div>
                <div class="card-actions">
                    ${cardMapBtn}
                    ${buildSaveButtons(r, 'card-save-actions')}
                </div>`;

            card.addEventListener('click', () => {
                focusRestaurant(r);
                container.querySelectorAll('.restaurant-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
            });

            container.appendChild(card);
        });

        container.querySelectorAll('.card-focus-btn').forEach(btn => {
            btn.addEventListener('click', e => {
                e.preventDefault();
                e.stopPropagation();
                const r = getRestaurantByUrl(decodeURIComponent(btn.dataset.focusUrl || ''));
                if (r) focusRestaurant(r);
            });
        });

        container.querySelectorAll('.save-btn').forEach(btn => {
            btn.addEventListener('click', e => {
                e.preventDefault();
                e.stopPropagation();
                handleSaveButtonClick(btn);
            });
        });
    }

    // === Focus on Restaurant ===
    function focusRestaurant(r) {
        if (!r.lat || !r.lng) return;
        map.setView([r.lat, r.lng], 16, { animate: true });
        const marker = markers.get(r.url);
        if (marker) {
            markerClusterGroup.zoomToShowLayer(marker, () => marker.openPopup());
        }
        if (window.innerWidth <= 768) togglePanel(false);
    }

    // === フィルタ全リセット ===
    function resetAllFilters() {
        activeRegion = 'all';
        activePrefecture = 'all';
        activeYear = 'all';
        countFilterMode = 'all';
        activeStatus = 'all';
        saveFilter = 'all';
        clearRadiusSearch(false);
        searchQuery = '';

        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = '';
        const prefSelect = document.getElementById('pref-select');
        if (prefSelect) prefSelect.value = 'all';

        document.querySelectorAll('.filter-btn').forEach(btn => {
            const isDefault = btn.dataset.filter === 'all' ||
                btn.dataset.year === 'all' ||
                btn.dataset.countMode === 'all';
            btn.classList.toggle('active', isDefault);
            btn.setAttribute('aria-pressed', isDefault ? 'true' : 'false');
        });

        setSegmentedButtons('.status-filters .filter-btn', 'all', 'status');
        setSegmentedButtons('.save-filters .filter-btn', 'all', 'saveFilter');

        rebuildYearButtons();
        map.flyTo(JAPAN_CENTER, JAPAN_ZOOM, { duration: 0.8 });
        applyFilters();
    }

    // === UI Updates ===
    function updateStats() {
        const src = getCategorySource();
        const total = src.length;
        const east   = src.filter(r => r.region === 'EAST').length;
        const west   = src.filter(r => r.region === 'WEST').length;
        const kagawa = src.filter(r => r.region === 'KAGAWA').length;

        animateNumber('stat-total', total);
        animateNumber('stat-east', east);
        animateNumber('stat-west', west);
        animateNumber('stat-kagawa', kagawa);

        // KAGAWAがそばカテゴリ表示時は非表示（そばにKAGAWAなし）
        const kagawaEl = document.getElementById('stat-kagawa')?.closest('.stat-item');
        if (kagawaEl) kagawaEl.style.display = (activeCategory === 'soba') ? 'none' : '';
    }

    function animateNumber(elementId, target) {
        const el = document.getElementById(elementId);
        if (!el) return;
        const nextValue = Number(target) || 0;
        const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
        const currentState = numberAnimationState.get(elementId);
        if (currentState?.frameId) cancelAnimationFrame(currentState.frameId);

        const previousValue = currentState?.value ?? parseInt(el.textContent.replace(/[^\d-]/g, ''), 10) ?? 0;
        if (prefersReducedMotion || previousValue === nextValue) {
            el.textContent = nextValue.toLocaleString('ja-JP');
            numberAnimationState.set(elementId, { value: nextValue, frameId: null });
            return;
        }

        const duration = Math.min(900, Math.max(360, 220 + Math.abs(nextValue - previousValue) * 8));
        const start = performance.now();
        el.classList.remove('number-rolling');
        void el.offsetWidth;
        el.classList.add('number-rolling');

        function tick(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = Math.round(previousValue + (nextValue - previousValue) * eased);
            el.textContent = value.toLocaleString('ja-JP');
            numberAnimationState.set(elementId, { value, frameId: null });
            if (progress < 1) {
                const frameId = requestAnimationFrame(tick);
                numberAnimationState.set(elementId, { value, frameId });
            } else {
                el.textContent = nextValue.toLocaleString('ja-JP');
                el.classList.remove('number-rolling');
                numberAnimationState.set(elementId, { value: nextValue, frameId: null });
            }
        }

        const frameId = requestAnimationFrame(tick);
        numberAnimationState.set(elementId, { value: previousValue, frameId });
    }

    function getViewportBounds() {
        if (!map) return null;
        const bounds = map.getBounds();
        const zoom = map.getZoom();
        const paddingRatio = zoom <= 7 ? 0.18 : zoom <= 10 ? 0.1 : 0.04;
        return bounds.pad(paddingRatio);
    }

    function getRestaurantsInViewport() {
        const bounds = getViewportBounds();
        if (!bounds) return filteredRestaurants;
        return filteredRestaurants.filter(r =>
            r.lat != null &&
            r.lng != null &&
            bounds.contains([r.lat, r.lng])
        );
    }

    function updateMapViewportState() {
        visibleRestaurants = getRestaurantsInViewport();
        updateVisibleCount();
        renderList();
    }

    function updateVisibleCount() {
        const totalEl = document.getElementById('visible-count');
        const mapEl = document.getElementById('map-visible-count');
        animateNumber('visible-count', filteredRestaurants.length);
        animateNumber('map-visible-count', visibleRestaurants.length);
    }

    function setSegmentedButtons(selector, activeValue, datasetKey) {
        document.querySelectorAll(selector).forEach(btn => {
            const isActive = btn.dataset[datasetKey] === activeValue;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });
    }

    // === 現在地機能 ===
    let userLocationCircle = null;

    function locateUser() {
        const btn = document.getElementById('locate-btn');
        if (!navigator.geolocation) { alert('お使いのブラウザは位置情報に対応していません'); return; }

        btn.classList.add('locating');

        navigator.geolocation.getCurrentPosition(
            function (position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const accuracy = position.coords.accuracy;

                if (userLocationCircle) map.removeLayer(userLocationCircle);
                userLocationCircle = L.circle([lat, lng], {
                    radius: accuracy, fillColor: '#4285F4', fillOpacity: 0.1,
                    color: '#4285F4', weight: 1, opacity: 0.3
                }).addTo(map);

                setDistanceOrigin('current', lat, lng, accuracy);
                btn.classList.remove('locating');
            },
            function (error) {
                btn.classList.remove('locating');
                const msgs = {
                    [error.PERMISSION_DENIED]: '位置情報の使用が許可されていません。\nブラウザの設定から位置情報を許可してください。',
                    [error.POSITION_UNAVAILABLE]: '現在地を取得できませんでした。',
                    [error.TIMEOUT]: '位置情報の取得がタイムアウトしました。',
                };
                alert(msgs[error.code] || '位置情報の取得に失敗しました。');
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
        );
    }

    // === 任意地点からの半径検索 ===
    function handleMapClick(e) {
        if (!radiusPickMode) return;
        setDistanceOrigin('picked', e.latlng.lat, e.latlng.lng);
    }

    function setDistanceOrigin(type, lat, lng, accuracy = null) {
        const label = type === 'current' ? '現在地' : '指定地点';
        radiusPickMode = false;
        if (type !== 'current' && userLocationCircle) {
            map.removeLayer(userLocationCircle);
            userLocationCircle = null;
        }
        distanceOrigin = { type, lat, lng, label, accuracy };
        updateDistanceControls();
        updateRadiusOverlay();
        enableDistanceSort(`${label}から近い順 ${type === 'current' ? '📍' : '📌'}`);
        sortMode = 'distance';
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) sortSelect.value = 'distance';
        applyFilters();
        map.flyTo([lat, lng], Math.max(map.getZoom(), 13), { duration: 0.8 });
    }

    function updateRadiusOverlay() {
        if (radiusMarker) map.removeLayer(radiusMarker);
        if (radiusCircle) map.removeLayer(radiusCircle);

        const clearBtn = document.getElementById('radius-clear-btn');
        const summary = document.getElementById('radius-summary');
        if (!distanceOrigin) {
            if (clearBtn) clearBtn.disabled = true;
            if (summary) summary.textContent = '起点未指定';
            return;
        }

        const isCurrent = distanceOrigin.type === 'current';
        const fillColor = isCurrent ? '#4285F4' : '#E8C547';
        const lineColor = isCurrent ? '#4285F4' : '#D4A853';

        radiusMarker = L.circleMarker([distanceOrigin.lat, distanceOrigin.lng], {
            radius: isCurrent ? 8 : 7,
            fillColor,
            color: '#ffffff',
            weight: 2,
            fillOpacity: 1
        }).addTo(map);
        radiusMarker.bindPopup(`<strong>${isCurrent ? '📍 現在地' : '📌 検索起点'}</strong>`);

        if (radiusKm !== 'none') {
            radiusCircle = L.circle([distanceOrigin.lat, distanceOrigin.lng], {
                radius: radiusKm * 1000,
                fillColor,
                fillOpacity: 0.08,
                color: lineColor,
                weight: 2,
                opacity: 0.65
            }).addTo(map);
        }

        if (clearBtn) clearBtn.disabled = false;
        if (summary) {
            summary.textContent = radiusKm === 'none'
                ? `${distanceOrigin.label}から近い順`
                : `${distanceOrigin.label}から${radiusKm}km以内`;
        }
    }

    function clearRadiusSearch(shouldApply = true) {
        distanceOrigin = null;
        radiusPickMode = false;
        if (radiusMarker) map.removeLayer(radiusMarker);
        if (radiusCircle) map.removeLayer(radiusCircle);
        if (userLocationCircle) map.removeLayer(userLocationCircle);
        radiusMarker = null;
        radiusCircle = null;
        userLocationCircle = null;
        updateRadiusOverlay();
        updateDistanceControls();
        if (sortMode === 'distance') {
            sortMode = 'name';
            const sortSelect = document.getElementById('sort-select');
            if (sortSelect) sortSelect.value = 'name';
        }
        disableDistanceSort();
        if (shouldApply) applyFilters();
    }

    function enableDistanceSort(label) {
        const sortSelect = document.getElementById('sort-select');
        const distOption = sortSelect ? sortSelect.querySelector('option[value="distance"]') : null;
        if (distOption) {
            distOption.removeAttribute('disabled');
            distOption.textContent = label;
        }
    }

    function disableDistanceSort() {
        const sortSelect = document.getElementById('sort-select');
        const distOption = sortSelect ? sortSelect.querySelector('option[value="distance"]') : null;
        if (distOption) {
            distOption.setAttribute('disabled', 'disabled');
            distOption.textContent = '近い順（起点指定後）';
        }
    }

    function syncDistanceSortControl() {
        if (distanceOrigin) {
            enableDistanceSort(`${distanceOrigin.label}から近い順 ${distanceOrigin.type === 'current' ? '📍' : '📌'}`);
            return;
        }

        const sortSelect = document.getElementById('sort-select');
        const distOption = sortSelect ? sortSelect.querySelector('option[value="distance"]') : null;
        if (!sortSelect || !distOption) return;

        if (searchDistanceSortActive) {
            distOption.removeAttribute('disabled');
            distOption.textContent = '検索結果から近い順';
            sortSelect.value = 'distance';
            return;
        }

        disableDistanceSort();
        if (sortSelect.value === 'distance') sortSelect.value = sortMode === 'distance' ? 'name' : sortMode;
    }

    function updateDistanceControls() {
        const currentBtn = document.getElementById('radius-current-btn');
        const pickBtn = document.getElementById('radius-pick-btn');
        if (currentBtn) {
            const isActive = !radiusPickMode && distanceOrigin?.type === 'current';
            currentBtn.classList.toggle('active', isActive);
            currentBtn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        }
        if (pickBtn) {
            const isActive = radiusPickMode || distanceOrigin?.type === 'picked';
            pickBtn.classList.toggle('active', isActive);
            pickBtn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        }
    }

    // === Panel Toggle ===
    function togglePanel(forceOpen) {
        const panel = document.getElementById('control-panel');
        if (!panel) return;
        const isOpen = panel.classList.contains('panel-open');
        const mobileBtn = document.getElementById('mobile-panel-toggle');
        const toggleLabel = document.querySelector('.toggle-label');
        const toggleIcon = document.querySelector('.toggle-icon');
        const isMobile = window.innerWidth <= 768;

        if (forceOpen === true || (!isOpen && forceOpen !== false)) {
            panel.classList.remove('panel-closed');
            panel.classList.add('panel-open');
            if (mobileBtn) mobileBtn.classList.add('mobile-toggle-hidden');
            if (isMobile) {
                if (toggleLabel) toggleLabel.textContent = '閉じる';
                if (toggleIcon) toggleIcon.textContent = '🔽';
            }
        } else {
            panel.classList.remove('panel-open');
            panel.classList.add('panel-closed');
            if (mobileBtn) mobileBtn.classList.remove('mobile-toggle-hidden');
            if (isMobile) {
                if (toggleLabel) toggleLabel.textContent = '🔍 検索・フィルタ';
                if (toggleIcon) toggleIcon.textContent = '◀';
            }
        }
        setTimeout(() => map.invalidateSize(), 350);
    }

    // === Event Binding ===
    function bindEvents() {
        // ロゴクリックでリセット
        const logoHome = document.getElementById('logo-home');
        if (logoHome) {
            const goHome = () => { window.location.href = window.location.pathname; };
            logoHome.addEventListener('click', goHome);
            logoHome.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); goHome(); }
            });
        }

        // カテゴリ切替
        document.querySelectorAll('.cat-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.cat-btn').forEach(b => {
                    b.classList.remove('active');
                    b.setAttribute('aria-pressed', 'false');
                });
                this.classList.add('active');
                this.setAttribute('aria-pressed', 'true');
                activeCategory = this.dataset.cat;

                // カテゴリ変更時: 年度リセット・都道府県リセット
                activeYear = 'all';
                activePrefecture = 'all';
                const prefSelect = document.getElementById('pref-select');
                if (prefSelect) prefSelect.value = 'all';

                rebuildYearButtons();
                populateFilters();
                updateStats();
                updateLogoForCategory();

                // ヘッダーのカテゴリカラー切替
                document.documentElement.setAttribute('data-category', activeCategory);

                applyFilters();
            });
        });

        // Panel toggle
        const panelToggle = document.getElementById('panel-toggle');
        if (panelToggle) panelToggle.addEventListener('click', () => togglePanel());

        const mobileToggle = document.getElementById('mobile-panel-toggle');
        if (mobileToggle) mobileToggle.addEventListener('click', () => togglePanel(true));

        const locateBtn = document.getElementById('locate-btn');
        if (locateBtn) locateBtn.addEventListener('click', () => locateUser());

        // フィルタ折りたたみ
        document.querySelectorAll('.section-toggle').forEach(toggle => {
            const updateToggleText = () => {
                const text = toggle.querySelector('.section-toggle-text');
                if (text) text.textContent = toggle.getAttribute('aria-expanded') === 'true' ? '閉じる' : '開く';
            };
            updateToggleText();
            toggle.addEventListener('click', function () {
                const body = document.getElementById(this.getAttribute('aria-controls'));
                if (!body) return;
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', !isExpanded);
                body.classList.toggle('collapsed', isExpanded);
                updateToggleText();
            });
        });

        // パネル幅リサイズ（PC用）
        const resizeHandle = document.getElementById('panel-resize-handle');
        if (resizeHandle && window.innerWidth > 768) {
            let isResizing = false, startX = 0, startWidth = 0;
            resizeHandle.addEventListener('mousedown', e => {
                e.preventDefault();
                isResizing = true;
                startX = e.clientX;
                startWidth = document.getElementById('control-panel').offsetWidth;
                document.body.classList.add('panel-resizing');
                resizeHandle.classList.add('dragging');
            });
            document.addEventListener('mousemove', e => {
                if (!isResizing) return;
                e.preventDefault();
                const newWidth = Math.max(280, Math.min(600, startWidth + e.clientX - startX));
                const panel = document.getElementById('control-panel');
                panel.style.width = newWidth + 'px';
                document.documentElement.style.setProperty('--panel-width', newWidth + 'px');
                map.invalidateSize();
            });
            document.addEventListener('mouseup', () => {
                if (!isResizing) return;
                isResizing = false;
                document.body.classList.remove('panel-resizing');
                resizeHandle.classList.remove('dragging');
                map.invalidateSize();
            });
        }

        // Region filter
        document.querySelectorAll('.region-filters .filter-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.region-filters .filter-btn').forEach(b => {
                    b.classList.remove('active'); b.setAttribute('aria-pressed', 'false');
                });
                this.classList.add('active');
                this.setAttribute('aria-pressed', 'true');
                activeRegion = this.dataset.filter;
                applyFilters();
            });
        });

        // Prefecture filter
        const prefSelect = document.getElementById('pref-select');
        if (prefSelect) {
            prefSelect.addEventListener('change', function () {
                activePrefecture = this.value;
                applyFilters();
            });
        }

        // Count filter
        document.querySelectorAll('.count-filters .filter-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.count-filters .filter-btn').forEach(b => {
                    b.classList.remove('active'); b.setAttribute('aria-pressed', 'false');
                });
                this.classList.add('active');
                this.setAttribute('aria-pressed', 'true');
                countFilterMode = this.dataset.countMode || 'all';
                applyFilters();
            });
        });

        // Business status filter
        document.querySelectorAll('.status-filters .filter-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.status-filters .filter-btn').forEach(b => {
                    b.classList.remove('active'); b.setAttribute('aria-pressed', 'false');
                });
                this.classList.add('active');
                this.setAttribute('aria-pressed', 'true');
                activeStatus = this.dataset.status || 'all';
                applyFilters();
            });
        });

        // Save state filter
        document.querySelectorAll('.save-filters .filter-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.save-filters .filter-btn').forEach(b => {
                    b.classList.remove('active'); b.setAttribute('aria-pressed', 'false');
                });
                this.classList.add('active');
                this.setAttribute('aria-pressed', 'true');
                saveFilter = this.dataset.saveFilter || 'all';
                applyFilters();
            });
        });

        const saveExportBtn = document.getElementById('save-export-btn');
        if (saveExportBtn) saveExportBtn.addEventListener('click', exportSavedStates);

        const saveImportBtn = document.getElementById('save-import-btn');
        const saveImportInput = document.getElementById('save-import-input');
        if (saveImportBtn && saveImportInput) {
            saveImportBtn.addEventListener('click', () => saveImportInput.click());
            saveImportInput.addEventListener('change', function () {
                const file = this.files && this.files[0];
                if (file) handleImportFile(file);
                this.value = '';
            });
        }

        const radiusPickBtn = document.getElementById('radius-pick-btn');
        if (radiusPickBtn) {
            radiusPickBtn.addEventListener('click', function () {
                radiusPickMode = !radiusPickMode;
                updateDistanceControls();
            });
        }

        const radiusCurrentBtn = document.getElementById('radius-current-btn');
        if (radiusCurrentBtn) radiusCurrentBtn.addEventListener('click', () => locateUser());

        const radiusClearBtn = document.getElementById('radius-clear-btn');
        if (radiusClearBtn) radiusClearBtn.addEventListener('click', () => clearRadiusSearch());

        const radiusSelect = document.getElementById('radius-select');
        if (radiusSelect) {
            radiusSelect.addEventListener('change', function () {
                radiusKm = this.value === 'none' ? 'none' : (parseFloat(this.value) || 5);
                updateRadiusOverlay();
                if (distanceOrigin) applyFilters();
            });
        }

        document.addEventListener('click', e => {
            const saveBtn = e.target.closest('.leaflet-popup .save-btn');
            if (!saveBtn) return;
            e.preventDefault();
            e.stopPropagation();
            handleSaveButtonClick(saveBtn);
        });

        // Sort
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', function () {
                sortMode = this.value;
                applyFilters();
            });
        }

        // Search (debounce 200ms)
        let searchTimeout;
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', function () {
                clearTimeout(searchTimeout);
                const val = this.value;
                searchTimeout = setTimeout(() => {
                    searchQuery = val.trim();
                    applyFilters();
                }, 200);
            });
        }

        // キーボードショートカット
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') togglePanel(false);
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                togglePanel(true);
                const si = document.getElementById('search-input');
                if (si) si.focus();
            }
        });

        // フッター免責トグル
        const footerToggle = document.getElementById('footer-toggle');
        const appFooter = document.getElementById('app-footer');
        if (footerToggle && appFooter) {
            footerToggle.addEventListener('click', () => {
                const isOpen = appFooter.classList.toggle('show');
                footerToggle.textContent = isOpen ? '✕ 閉じる' : 'ℹ️ 免責・出典';
            });
        }

        const bannerClose = document.getElementById('app-banner-close');
        if (bannerClose) bannerClose.addEventListener('click', hideAppBanner);

        window.addEventListener('offline', () => {
            showOfflineBanner('現在オフラインです。地図は表示できない場合がありますが、読み込み済みの店舗リストは利用できます。');
        });
        window.addEventListener('online', () => {
            tileErrorCount = 0;
            hideOfflineBanner();
        });
        if (!navigator.onLine) {
            showOfflineBanner('現在オフラインです。地図は表示できない場合がありますが、読み込み済みの店舗リストは利用できます。');
        }
    }

    // === Utility ===
    function isSafeUrl(url) {
        if (!url || typeof url !== 'string') return false;
        try {
            const parsed = new URL(url);
            return parsed.protocol === 'https:' && parsed.hostname.endsWith('tabelog.com');
        } catch { return false; }
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.add('hidden');
    }

    function showLoadingError(message) {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        if (loadingText) loadingText.textContent = message;
        if (overlay) overlay.classList.add('error');
    }

    function registerServiceWorker() {
        if (!('serviceWorker' in navigator)) return;
        navigator.serviceWorker.register('sw.js').then(registration => {
            if (registration.waiting && navigator.serviceWorker.controller) {
                notifyServiceWorkerUpdate();
            }
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                if (!newWorker) return;
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        notifyServiceWorkerUpdate();
                    }
                });
            });
        }).catch(error => {
            console.warn('Service Worker registration failed:', error);
        });
    }

    function notifyServiceWorkerUpdate() {
        if (swRefreshPending) return;
        swRefreshPending = true;
        showAppBanner(
            '新しいデータまたは機能が利用できます。最新版に更新できます。',
            '更新',
            () => location.reload()
        );
    }

    function showOfflineBanner(message) {
        showAppBanner(message, null, null, 'offline');
    }

    function hideOfflineBanner() {
        const banner = document.getElementById('app-banner');
        if (banner && banner.dataset.kind === 'offline') hideAppBanner();
    }

    function showAppBanner(message, actionLabel, actionHandler, kind = 'info') {
        const banner = document.getElementById('app-banner');
        const messageEl = document.getElementById('app-banner-message');
        const actionBtn = document.getElementById('app-banner-action');
        if (!banner || !messageEl || !actionBtn) return;

        banner.dataset.kind = kind;
        banner.hidden = false;
        banner.classList.add('show');
        messageEl.textContent = message;

        if (actionLabel && actionHandler) {
            actionBtn.hidden = false;
            actionBtn.textContent = actionLabel;
            actionBtn.onclick = actionHandler;
        } else {
            actionBtn.hidden = true;
            actionBtn.onclick = null;
        }
    }

    function hideAppBanner() {
        const banner = document.getElementById('app-banner');
        const actionBtn = document.getElementById('app-banner-action');
        if (!banner) return;
        banner.classList.remove('show');
        banner.hidden = true;
        banner.dataset.kind = '';
        if (actionBtn) actionBtn.onclick = null;
    }

    function toCssClass(value) {
        return String(value || '').toLowerCase().replace(/[^a-z0-9_-]/g, '');
    }

    // === Start ===
    document.addEventListener('DOMContentLoaded', init);

})();
