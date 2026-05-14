const PREFIX_WEIGHTS = {
    genre: 0.9,
    style: 1.45,
    texture: 1.45,
    dish: 1.35,
    lineage: 1.3,
    scene: 1.08,
    mood: 1.15,
    pref: 0.42,
    macro_area: 0.32,
    selection: 0.34,
    region: 0.25,
    status: 0
};

const REASON_PRIORITY = {
    style: 1.6,
    texture: 1.55,
    dish: 1.5,
    lineage: 1.4,
    scene: 1.15,
    mood: 1.1,
    genre: 0,
    selection: 0.55,
    pref: 0,
    macro_area: 0,
    region: 0,
    status: 0
};

const EXTERNAL_SIGNAL_SCORE_BOOST = 1.06;
const EXTERNAL_REASON_BOOST = 1.5;
const MODEL_REASON_PENALTY = 0.72;
const PRIMARY_REASON_PREFIXES = new Set(['style', 'texture', 'dish', 'mood', 'scene', 'lineage']);
const FACT_LABEL_PATTERN = /^(うどん|そば|北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県|EAST|WEST|KAGAWA|\d回以上選出)$/;

export function createRecommendationIndex(tagData) {
    if (!Array.isArray(tagData?.restaurants)) {
        throw new Error('Recommendation tag data should contain restaurants array');
    }
    const tagDefinitions = tagData.tagDefinitions || {};
    const affinityGroups = Array.isArray(tagData.affinityGroups) ? tagData.affinityGroups : [];
    const tagsByUrl = new Map(
        tagData.restaurants
            .filter(item => item?.url && Array.isArray(item.tags))
            .map(item => [item.url, item])
    );
    return {
        tagDefinitions,
        affinityGroups,
        affinityByUrl: buildAffinityIndex(affinityGroups),
        tagsByUrl
    };
}

export function getRecommendations({
    source,
    restaurants = [],
    index,
    mode = 'similar',
    limit = 4,
    savedStates = {},
    calcDistance
}) {
    if (!source?.url || !index?.tagsByUrl?.has(source.url)) return [];
    const sourceRecord = index.tagsByUrl.get(source.url);
    const preferenceTags = buildSavedPreferenceTagMap(index, savedStates, source.url);

    const recommendations = restaurants
        .filter(candidate => candidate.url !== source.url)
        .filter(candidate => !candidate.closed)
        .map(candidate => {
            const candidateRecord = index.tagsByUrl.get(candidate.url);
            if (!candidateRecord) return null;
            const scored = scoreCandidate(source, sourceRecord, candidate, candidateRecord, {
                index,
                mode,
                preferenceTags,
                savedStates,
                calcDistance
            });
            return scored && scored.score > 0.02 ? scored : null;
        })
        .filter(Boolean)
        .sort((a, b) => b.score - a.score)
        .slice(0, limit);

    return normalizeDisplayScores(recommendations);
}

function scoreCandidate(source, sourceRecord, candidate, candidateRecord, options) {
    const { index, mode, preferenceTags, savedStates, calcDistance } = options;
    const sourceTags = buildTagMap(sourceRecord);
    const candidateTags = buildTagMap(candidateRecord);
    if (!sourceTags.size || !candidateTags.size) return null;

    let dot = 0;
    let normA = 0;
    let normB = 0;
    const shared = [];

    sourceTags.forEach((aTag, key) => {
        const weight = getTagWeight(key, mode);
        const aValue = getTagStrength(aTag);
        normA += (aValue ** 2) * weight;
    });
    candidateTags.forEach((bTag, key) => {
        const weight = getTagWeight(key, mode);
        const bValue = getTagStrength(bTag);
        normB += (bValue ** 2) * weight;
    });
    sourceTags.forEach((aTag, key) => {
        if (!candidateTags.has(key)) return;
        const weight = getTagWeight(key, mode);
        const bTag = candidateTags.get(key);
        const aValue = getTagStrength(aTag);
        const bValue = getTagStrength(bTag);
        const contribution = aValue * bValue * weight;
        dot += contribution;
        if (weight > 0) {
            shared.push({
                key,
                contribution,
                sourceSource: getTagSource(aTag),
                candidateSource: getTagSource(bTag),
                sourceHasExternal: hasExternalEvidence(aTag),
                candidateHasExternal: hasExternalEvidence(bTag)
            });
        }
    });

    if (!dot || !normA || !normB) return null;

    const similarity = dot / Math.sqrt(normA * normB);
    if (mode === 'nearby' && similarity < 0.18) return null;

    const distanceKm = getDistanceKm(source, candidate, calcDistance);
    const distanceScore = Number.isFinite(distanceKm) ? 1 / (1 + distanceKm / 18) : 0;

    let score = similarity;
    if (mode === 'nearby') {
        score = (similarity * 0.5) + (distanceScore * 0.5);
    } else if (mode === 'expand') {
        const sameCategory = source.category === candidate.category;
        const samePrefecture = source.prefecture === candidate.prefecture;
        const noveltyFactor = (sameCategory ? 0.94 : 1.08) * (samePrefecture ? 0.96 : 1.03);
        score = similarity * noveltyFactor;
    }

    const affinityBoost = getAffinityBoost(index, source.url, candidate.url, mode);
    if (affinityBoost > 0) score *= 1 + affinityBoost;

    if (preferenceTags?.size) {
        const preferenceSimilarity = calculateMapSimilarity(preferenceTags, candidateTags, mode);
        if (preferenceSimilarity > 0.05) score *= 1 + Math.min(0.1, preferenceSimilarity * 0.12);
    }

    if (savedStates?.[candidate.url] === 'want') score *= 1.08;

    const reasons = buildReasons(shared, sourceTags, candidateTags, mode, index.tagDefinitions);
    return {
        restaurant: candidate,
        score,
        distanceKm,
        reasons,
        reasonText: formatReason(reasons),
        affinityBoost
    };
}

function getDistanceKm(source, candidate, calcDistance) {
    if (
        typeof calcDistance !== 'function'
        || source.lat == null
        || source.lng == null
        || candidate.lat == null
        || candidate.lng == null
    ) {
        return Infinity;
    }
    return calcDistance(source.lat, source.lng, candidate.lat, candidate.lng);
}

function normalizeDisplayScores(items) {
    if (!items.length) return items;
    const max = Math.max(...items.map(item => item.score));
    const min = Math.min(...items.map(item => item.score));
    const spread = max - min;
    return items.map((item, index) => {
        const rankScore = Math.max(72, 96 - (index * 4));
        const valueScore = spread > 0.03
            ? 72 + (((item.score - min) / spread) * 24)
            : rankScore;
        return {
            ...item,
            displayScore: Math.round(Math.max(72, Math.min(96, (valueScore * 0.62) + (rankScore * 0.38))))
        };
    });
}

function buildSavedPreferenceTagMap(index, savedStates, excludedUrl = '') {
    const aggregate = new Map();
    let count = 0;
    Object.entries(savedStates || {}).forEach(([url, state]) => {
        if (state !== 'want' || url === excludedUrl) return;
        const record = index.tagsByUrl.get(url);
        if (!record) return;
        const tagMap = buildTagMap(record);
        let used = false;
        tagMap.forEach((tagItem, key) => {
            const prefix = getTagPrefix(key);
            if (!PRIMARY_REASON_PREFIXES.has(prefix) && prefix !== 'genre') return;
            aggregate.set(key, (aggregate.get(key) || 0) + getTagStrength(tagItem));
            used = true;
        });
        if (used) count += 1;
    });
    if (!count) return new Map();
    aggregate.forEach((value, key) => aggregate.set(key, value / count));
    return aggregate;
}

function calculateMapSimilarity(aTags, bTags, mode = 'similar') {
    if (!aTags?.size || !bTags?.size) return 0;
    let dot = 0;
    let normA = 0;
    let normB = 0;
    aTags.forEach((aTag, key) => {
        const weight = getTagWeight(key, mode);
        const aValue = getTagStrength(aTag);
        normA += (aValue ** 2) * weight;
        if (bTags.has(key)) dot += aValue * getTagStrength(bTags.get(key)) * weight;
    });
    bTags.forEach((bTag, key) => {
        const weight = getTagWeight(key, mode);
        const bValue = getTagStrength(bTag);
        normB += (bValue ** 2) * weight;
    });
    return dot && normA && normB ? dot / Math.sqrt(normA * normB) : 0;
}

function buildAffinityIndex(groups) {
    const index = new Map();
    groups.forEach(group => {
        if (!Array.isArray(group?.urls) || group.urls.length < 2) return;
        group.urls.forEach(url => {
            const items = index.get(url) || [];
            items.push(group);
            index.set(url, items);
        });
    });
    return index;
}

function getAffinityBoost(index, sourceUrl, candidateUrl, mode) {
    const groups = index.affinityByUrl.get(sourceUrl);
    if (!groups?.length) return 0;
    let boost = 0;
    groups.forEach(group => {
        if (!Array.isArray(group.urls) || !group.urls.includes(candidateUrl)) return;
        if (Array.isArray(group.modes) && !group.modes.includes(mode)) return;
        boost += Number(group.boost) || 0;
    });
    return Math.min(0.16, boost);
}

function buildTagMap(record) {
    const map = new Map();
    (record?.tags || []).forEach(tag => {
        const key = String(tag?.key || '');
        const prefix = getTagPrefix(key);
        if (!key || prefix === 'status') return;
        const weight = Number(tag.weight);
        const confidence = Number(tag.confidence);
        if (!Number.isFinite(weight) || !Number.isFinite(confidence)) return;
        const source = String(tag.source || '');
        const hasExternalEvidence = source === 'external_signal'
            || (Array.isArray(tag.evidence) && tag.evidence.some(item => String(item || '').startsWith('external')));
        const baseStrength = Math.max(0, weight) * Math.max(0, confidence);
        const sourceBoost = hasExternalEvidence && PRIMARY_REASON_PREFIXES.has(prefix)
            ? EXTERNAL_SIGNAL_SCORE_BOOST
            : 1;
        map.set(key, {
            strength: baseStrength * sourceBoost,
            source,
            hasExternalEvidence,
            rawStrength: baseStrength
        });
    });
    return map;
}

function getTagStrength(tagItem) {
    if (typeof tagItem === 'number') return tagItem;
    const value = Number(tagItem?.strength);
    return Number.isFinite(value) ? value : 0;
}

function getTagSource(tagItem) {
    return typeof tagItem === 'object' && tagItem ? String(tagItem.source || '') : '';
}

function hasExternalEvidence(tagItem) {
    return Boolean(typeof tagItem === 'object' && tagItem && tagItem.hasExternalEvidence);
}

function getTagPrefix(key) {
    return String(key || '').split('.')[0];
}

function getTagWeight(key, mode) {
    const prefix = getTagPrefix(key);
    const base = PREFIX_WEIGHTS[prefix] ?? 0.6;
    if (base <= 0) return 0;
    return base * getModeFactor(prefix, mode);
}

function getModeFactor(prefix, mode) {
    if (mode === 'nearby') {
        if (prefix === 'pref' || prefix === 'macro_area') return 1.12;
        if (prefix === 'region') return 0.85;
        if (prefix === 'genre') return 0.82;
        if (prefix === 'style' || prefix === 'texture' || prefix === 'dish') return 1.04;
    }
    if (mode === 'expand') {
        if (prefix === 'genre') return 0.58;
        if (prefix === 'pref') return 0.22;
        if (prefix === 'macro_area' || prefix === 'region') return 0.58;
        if (prefix === 'style' || prefix === 'texture' || prefix === 'dish' || prefix === 'lineage') return 1.22;
        if (prefix === 'scene' || prefix === 'mood') return 1.12;
    }
    return 1;
}

function buildReasons(shared, sourceTags, candidateTags, mode, tagDefinitions) {
    const reasonItems = shared
        .map(item => {
            const prefix = getTagPrefix(item.key);
            const label = tagDefinitions[item.key]?.label || item.key;
            const sourceTag = sourceTags.get(item.key);
            const candidateTag = candidateTags.get(item.key);
            const hasExternalSignal = item.sourceHasExternal || item.candidateHasExternal;
            const isModelOnly = item.sourceSource === 'model_prior' && item.candidateSource === 'model_prior';
            let displayScore = item.contribution * (REASON_PRIORITY[prefix] ?? 0.7);
            if (hasExternalSignal) displayScore *= EXTERNAL_REASON_BOOST;
            if (isModelOnly) displayScore *= MODEL_REASON_PENALTY;
            const minStrength = Math.min(getTagStrength(sourceTag), getTagStrength(candidateTag));
            return { key: item.key, prefix, label, displayScore, minStrength, hasExternalSignal, isModelOnly };
        })
        .filter(item => item.prefix !== 'status')
        .filter(item => item.displayScore > 0)
        .sort((a, b) => b.displayScore - a.displayScore);
    const primaryReasons = reasonItems
        .filter(item => PRIMARY_REASON_PREFIXES.has(item.prefix))
        .filter(item => item.minStrength >= (mode === 'expand' ? 0.22 : 0.28))
        .slice(0, 3);
    const fallbackReasons = primaryReasons.length ? [] : reasonItems
        .filter(item => item.prefix === 'selection')
        .filter(item => item.minStrength >= 0.45)
        .slice(0, Math.max(0, 3 - primaryReasons.length));
    return [...primaryReasons, ...fallbackReasons].slice(0, 3).map(item => item.label);
}

function formatReason(reasons) {
    if (!reasons?.length) return '';
    const labels = reasons
        .filter(label => label && !FACT_LABEL_PATTERN.test(label))
        .slice(0, 3);
    return labels.length ? labels.join(' / ') : '';
}
