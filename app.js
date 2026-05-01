/**
 * うどん百名店 MAP - メインアプリケーション
 * Leaflet.js + MarkerCluster による地図ビジュアライゼーション
 * 2017〜2024 全年度統合版
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
    let activeYear = 'all';       // 年度フィルタ
    let minSelectCount = 0;       // 選出回数フィルタ
    let firstSelectedOnly = false;
    let hideClosedShops = false;   // 閉店除外フィルタ
    let searchQuery = '';
    let sortMode = 'name';        // ソートモード

    // === Map Tiles (国土地理院 淡色地図 - 全日本語表記) ===
    const TILE_URL = 'https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png';
    const TILE_ATTR = '<a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>';

    // === Japan Center ===
    const JAPAN_CENTER = [36.0, 137.0];
    const JAPAN_ZOOM = 6;

    // === Init ===
    async function init() {
        console.log('🚀 初期化開始');
        try {
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
            console.log('✅ 初期化完了');
        } catch (e) {
            console.error('❌ 初期化エラー:', e);
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
            maxZoom: 18
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
            // yearsフィールドがない店舗にはデフォルト[2024]を設定
            allRestaurants.forEach(r => {
                if (!r.years || !Array.isArray(r.years)) {
                    r.years = [2024];
                }
            });
            console.log(`📊 データ読込完了: ${allRestaurants.length} 店舗`);
        } catch (e) {
            console.error('❌ データ読込失敗:', e);
            // file:// プロトコル対策: XMLHttpRequest で再試行
            console.log('🔄 XMLHttpRequest で再試行...');
            try {
                allRestaurants = await loadDataXHR();
                allRestaurants.forEach(r => {
                    if (!r.years || !Array.isArray(r.years)) {
                        r.years = [2024];
                    }
                });
                console.log(`📊 XHR再試行成功: ${allRestaurants.length} 店舗`);
            } catch (e2) {
                console.error('❌ XHR再試行も失敗:', e2);
                allRestaurants = [];
            }
        }
    }

    // file:// プロトコル用のフォールバック
    function loadDataXHR() {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', 'data/restaurants.json', true);
            xhr.onload = function() {
                if (xhr.status === 200 || xhr.status === 0) { // status 0 = file:// protocol
                    try {
                        resolve(JSON.parse(xhr.responseText));
                    } catch (e) {
                        reject(e);
                    }
                } else {
                    reject(new Error(`XHR status: ${xhr.status}`));
                }
            };
            xhr.onerror = function() { reject(new Error('XHR error')); };
            xhr.send();
        });
    }

    // === Create Marker ===
    function createMarker(restaurant) {
        if (!restaurant.lat || !restaurant.lng) return null;

        const regionClass = restaurant.region.toLowerCase();
        const closedClass = restaurant.closed ? ' closed' : '';
        const selectCount = restaurant.years ? restaurant.years.length : 0;

        // 選出回数による強調クラス
        let selectClass = '';
        let markerSize = [28, 36];
        let anchorPos = [14, 36];
        if (selectCount >= 5) {
            selectClass = ' select-high';
            markerSize = [36, 44];
            anchorPos = [18, 44];
        } else if (selectCount >= 3) {
            selectClass = ' select-mid';
            markerSize = [32, 40];
            anchorPos = [16, 40];
        }

        const icon = L.divIcon({
            className: 'custom-marker',
            html: `<div class="marker-pin ${regionClass}${closedClass}${selectClass}">
                     <span class="marker-count">${selectCount}</span>
                   </div>`,
            iconSize: markerSize,
            iconAnchor: anchorPos,
            popupAnchor: [0, -anchorPos[1]]
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

    // === Build Year Badges ===
    function buildYearBadges(years) {
        if (!years || years.length === 0) return '';
        return years.map(y => {
            const shortYear = String(y).slice(2); // 2024 -> 24
            return `<span class="year-badge year-${y}">'${shortYear}</span>`;
        }).join('');
    }

    // === Build Popup Content ===
    function buildPopupContent(r) {
        const regionClass = r.region.toLowerCase();
        const selectCount = r.years ? r.years.length : 0;
        
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

        // 年度バッジ
        const yearBadgesHtml = buildYearBadges(r.years);

        // 選出回数テキスト
        const countText = selectCount > 0 ? `<span class="popup-select-count">${selectCount}回選出</span>` : '';

        return `
            <div class="popup-inner">
                <div class="popup-header">
                    <span class="popup-region-badge ${regionClass}">${r.region}</span>
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
        allRestaurants.forEach(r => {
            if (r.prefecture) prefSet.add(r.prefecture);
        });
        
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
            
            // Year filter（特定年度に選出されたもののみ表示）
            if (activeYear !== 'all') {
                const yearNum = parseInt(activeYear, 10);
                if (!r.years || !r.years.includes(yearNum)) return false;
            }

            // Min select count filter
            if (minSelectCount > 0) {
                const count = r.years ? r.years.length : 0;
                if (count < minSelectCount) return false;
            }
            
            // First selected filter
            if (firstSelectedOnly && !r.firstSelected) return false;

            // Hide closed shops
            if (hideClosedShops && r.closed) return false;
            
            // Search filter（ファジー検索: 駅名↔市区町村名の揺れに対応）
            if (searchQuery) {
                const q = searchQuery.toLowerCase();
                const area = (r.area || '');
                // 駅名から「駅」を除去したトークンも検索対象に追加
                const areaBase = area.replace(/駅$/, '').replace(/（.+?）/g, '');
                const searchTarget = `${r.name || ''} ${r.prefecture || ''} ${area} ${areaBase} ${r.holiday || ''} ${r.address || ''}`.toLowerCase();
                
                // クエリからも「市」「区」「町」「村」「駅」を除去してベーストークンを作成
                const qBase = q.replace(/[市区町村駅]$/g, '');
                
                // 完全一致 or ベーストークン一致
                if (!searchTarget.includes(q) && !searchTarget.includes(qBase)) return false;
            }
            
            return true;
        });

        // ソート適用
        sortRestaurants();

        renderMarkers();
        renderList();
        updateVisibleCount();
    }

    // === Sort ===
    function sortRestaurants() {
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
        }
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
            
            const selectCount = r.years ? r.years.length : 0;

            let badgesHtml = '';
            if (r.firstSelected) badgesHtml += '<span class="badge badge-new">NEW</span>';
            if (r.closed) badgesHtml += '<span class="badge badge-closed">閉店</span>';

            // 年度バッジ
            const yearBadgesHtml = buildYearBadges(r.years);

            // 選出回数バッジ
            const countBadgeClass = selectCount >= 5 ? 'count-badge-gold' : selectCount >= 3 ? 'count-badge-silver' : '';
            const countBadge = `<span class="count-badge ${countBadgeClass}">${selectCount}回</span>`;

            card.innerHTML = `
                <div class="card-region-dot ${r.region.toLowerCase()}"></div>
                <div class="card-info">
                    <div class="card-name">${escapeHtml(r.name)}</div>
                    <div class="card-area">${escapeHtml(r.prefecture)} ${escapeHtml(r.area)}</div>
                </div>
                <div class="card-right">
                    ${countBadge}
                    <div class="card-year-badges">${yearBadgesHtml}</div>
                    <div class="card-badges">${badgesHtml}</div>
                </div>
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
        if (!el) return;
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
        const el = document.getElementById('visible-count');
        if (el) el.textContent = filteredRestaurants.length;
    }

    // === 現在地機能 ===
    let userLocationMarker = null;
    let userLocationCircle = null;

    function locateUser() {
        const btn = document.getElementById('locate-btn');
        if (!navigator.geolocation) {
            alert('お使いのブラウザは位置情報に対応していません');
            return;
        }

        // ボタンにローディング状態を設定
        btn.classList.add('locating');

        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const accuracy = position.coords.accuracy;
                console.log('📍 現在地取得:', lat, lng, '精度:', accuracy + 'm');

                // 既存のマーカーを削除
                if (userLocationMarker) map.removeLayer(userLocationMarker);
                if (userLocationCircle) map.removeLayer(userLocationCircle);

                // 現在地マーカー（青い丸）
                userLocationMarker = L.circleMarker([lat, lng], {
                    radius: 8,
                    fillColor: '#4285F4',
                    color: '#ffffff',
                    weight: 3,
                    fillOpacity: 1,
                    className: 'user-location-marker'
                }).addTo(map);

                userLocationMarker.bindPopup(
                    '<div style="text-align:center;font-family:var(--font-main);">' +
                    '<strong>📍 現在地</strong><br>' +
                    '<span style="font-size:12px;color:#999;">精度: 約' + Math.round(accuracy) + 'm</span>' +
                    '</div>'
                );

                // 精度範囲の円
                userLocationCircle = L.circle([lat, lng], {
                    radius: accuracy,
                    fillColor: '#4285F4',
                    fillOpacity: 0.1,
                    color: '#4285F4',
                    weight: 1,
                    opacity: 0.3
                }).addTo(map);

                // ズームレベル14で現在地にフライ
                map.flyTo([lat, lng], 14, { duration: 1.5 });

                btn.classList.remove('locating');
            },
            function(error) {
                btn.classList.remove('locating');
                console.error('❌ 位置情報エラー:', error);
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        alert('位置情報の使用が許可されていません。\nブラウザの設定から位置情報を許可してください。');
                        break;
                    case error.POSITION_UNAVAILABLE:
                        alert('現在地を取得できませんでした。');
                        break;
                    case error.TIMEOUT:
                        alert('位置情報の取得がタイムアウトしました。');
                        break;
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
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
            // モバイルではラベルを「閉じる」に変更
            if (isMobile) {
                if (toggleLabel) toggleLabel.textContent = '閉じる';
                if (toggleIcon) toggleIcon.textContent = '🔽';
            }
        } else {
            panel.classList.remove('panel-open');
            panel.classList.add('panel-closed');
            if (mobileBtn) mobileBtn.classList.remove('mobile-toggle-hidden');
            // ラベルを元に戻す
            if (isMobile) {
                if (toggleLabel) toggleLabel.textContent = '🔍 検索・フィルタ';
                if (toggleIcon) toggleIcon.textContent = '◀';
            }
        }
        
        // 地図のリサイズ
        setTimeout(() => map.invalidateSize(), 350);
    }

    // === Event Binding ===
    function bindEvents() {
        console.log('🔗 イベントバインド開始');

        // Panel toggle
        const panelToggle = document.getElementById('panel-toggle');
        if (panelToggle) {
            panelToggle.addEventListener('click', () => togglePanel());
        }

        // モバイル用パネル開閉ボタン
        const mobileToggle = document.getElementById('mobile-panel-toggle');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', () => togglePanel(true));
        }

        // 現在地ボタン
        const locateBtn = document.getElementById('locate-btn');
        if (locateBtn) {
            locateBtn.addEventListener('click', () => locateUser());
        }

        // Region filter
        document.querySelectorAll('.region-filters .filter-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.region-filters .filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                activeRegion = this.dataset.filter;
                console.log('🔍 Region:', activeRegion);
                applyFilters();
            });
        });

        // Prefecture filter
        const prefSelect = document.getElementById('pref-select');
        if (prefSelect) {
            prefSelect.addEventListener('change', function() {
                activePrefecture = this.value;
                console.log('🔍 Prefecture:', activePrefecture);
                applyFilters();
            });
        }

        // Year filter（年度フィルタ）
        const yearBtns = document.querySelectorAll('.year-filters .filter-btn');
        console.log(`  年度ボタン: ${yearBtns.length} 個検出`);
        yearBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.year-filters .filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                activeYear = this.getAttribute('data-year');
                console.log('📅 Year filter:', activeYear);
                applyFilters();
            });
        });

        // Count filter（選出回数フィルタ）
        const countBtns = document.querySelectorAll('.count-filters .filter-btn');
        console.log(`  回数ボタン: ${countBtns.length} 個検出`);
        countBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.count-filters .filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                minSelectCount = parseInt(this.getAttribute('data-min-count'), 10) || 0;
                console.log('🏆 Count filter:', minSelectCount);
                applyFilters();
            });
        });

        // First selected filter
        const firstBtn = document.getElementById('first-selected-btn');
        if (firstBtn) {
            firstBtn.addEventListener('click', function() {
                firstSelectedOnly = !firstSelectedOnly;
                this.classList.toggle('active', firstSelectedOnly);
                console.log('⭐ First selected:', firstSelectedOnly);
                applyFilters();
            });
        }

        // Hide closed filter
        const closedBtn = document.getElementById('hide-closed-btn');
        if (closedBtn) {
            closedBtn.addEventListener('click', function() {
                hideClosedShops = !hideClosedShops;
                this.classList.toggle('active', hideClosedShops);
                console.log('🚫 Hide closed:', hideClosedShops);
                applyFilters();
            });
        }

        // Sort
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', function() {
                sortMode = this.value;
                console.log('📊 Sort:', sortMode);
                applyFilters();
            });
        }

        // Search
        let searchTimeout;
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                const input = this;
                searchTimeout = setTimeout(() => {
                    searchQuery = input.value.trim();
                    console.log('🔍 Search:', searchQuery);
                    applyFilters();
                }, 300);
            });
        }

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
                const si = document.getElementById('search-input');
                if (si) si.focus();
            }
        });

        console.log('✅ イベントバインド完了');
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
