/**
 * Search helpers for うどん・そば百名店 MAP.
 * Loaded before app.js as a small classic script to keep the main app script
 * compatible with the current GitHub Pages / Capacitor setup.
 */
(function (window) {
    'use strict';

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

    function toHiragana(value) {
        return String(value || '').replace(/[\u30a1-\u30f6]/g, ch =>
            String.fromCharCode(ch.charCodeAt(0) - 0x60)
        );
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

    window.HyakumeitenSearch = {
        normalizeSearchText,
        buildSearchQueries,
        isNameSearchMatch,
        isLocationSearchMatch,
        isSearchMatch
    };
})(window);
