let config = {};

function applyConfigToForm(cfg) {
    // LLM
    document.getElementById('llm-provider').value    = cfg.llm.provider    || '';
    document.getElementById('llm-model').value       = cfg.llm.model       || '';
    document.getElementById('llm-base-url').value    = cfg.llm.base_url    || '';
    document.getElementById('llm-api-key').value     = cfg.llm.api_key     || '';
    document.getElementById('llm-temperature').value = cfg.llm.temperature  ?? 0;
    document.getElementById('llm-max-tokens').value  = cfg.llm.max_tokens  || 2048;
    document.getElementById('llm-timeout').value     = cfg.llm.timeout     ?? 60;

    // Judge
    document.getElementById('judge-provider').value           = cfg.judge.provider    || '';
    document.getElementById('judge-model').value              = cfg.judge.model       || '';
    document.getElementById('judge-base-url').value           = cfg.judge.base_url    || '';
    document.getElementById('judge-api-key').value            = cfg.judge.api_key     || '';
    document.getElementById('judge-temperature').value        = cfg.judge.temperature ?? 0;
    document.getElementById('judge-timeout').value            = cfg.judge.timeout     ?? 60;
    document.getElementById('judge-max-tokens-d2').value      = cfg.judge.max_tokens_d2     ?? 100;
    document.getElementById('judge-max-tokens-d5').value      = cfg.judge.max_tokens_d5     ?? 300;
    document.getElementById('judge-max-input-chars-d5').value = cfg.judge.max_input_chars_d5 ?? 2000;

    // System Prompt
    document.getElementById('system-prompt').value = cfg.system_prompt || '';

    // Defenses
    document.getElementById('d1').checked = !!cfg.defenses.d1_input_filter;
    document.getElementById('d2').checked = !!cfg.defenses.d2_input_judge;
    document.getElementById('d3').checked = !!cfg.defenses.d3_sp_lock;
    document.getElementById('d4').checked = !!cfg.defenses.d4_sp_alignment;
    document.getElementById('d5').checked = !!cfg.defenses.d5_output_judge;
    document.getElementById('d6').checked = !!cfg.defenses.d6_output_sanitizer;

    // RAG
    document.getElementById('rag-enabled').checked           = !!cfg.rag.enabled;
    document.getElementById('rag-top-k').value               = cfg.rag.top_k ?? 3;
    document.getElementById('rag-distance-threshold').value  = cfg.rag.distance_threshold ?? 0.5;

    // RAG — Embedding
    const emb = cfg.rag.embedding || {};
    document.getElementById('rag-embedding-provider').value = emb.provider || 'openai';
    document.getElementById('rag-embedding-model').value    = emb.model    || 'text-embedding-3-small';
    document.getElementById('rag-embedding-base-url').value = emb.base_url || '';
    document.getElementById('rag-embedding-api-key').value  = emb.api_key  || '';
    document.getElementById('rag-embedding-timeout').value  = emb.timeout  ?? 60;
}

async function loadConfig() {
    try {
        const res = await fetch('/api/config', { cache: 'no-store' });
        config = await res.json();
        applyConfigToForm(config);
    } catch (err) {
        showToast(t('toast.load_error') + err.message);
        console.error('loadConfig error:', err);
    }
}

async function saveConfig() {
    try {
        // LLM
        config.llm.provider    = document.getElementById('llm-provider').value;
        config.llm.model       = document.getElementById('llm-model').value;
        config.llm.base_url    = document.getElementById('llm-base-url').value;
        config.llm.api_key     = document.getElementById('llm-api-key').value;
        config.llm.temperature = parseFloat(document.getElementById('llm-temperature').value);
        config.llm.max_tokens  = parseInt(document.getElementById('llm-max-tokens').value);
        config.llm.timeout     = parseInt(document.getElementById('llm-timeout').value);

        // Judge
        config.judge.provider           = document.getElementById('judge-provider').value;
        config.judge.model              = document.getElementById('judge-model').value;
        config.judge.base_url           = document.getElementById('judge-base-url').value;
        config.judge.api_key            = document.getElementById('judge-api-key').value;
        config.judge.temperature        = parseFloat(document.getElementById('judge-temperature').value);
        config.judge.timeout            = parseInt(document.getElementById('judge-timeout').value);
        config.judge.max_tokens_d2      = parseInt(document.getElementById('judge-max-tokens-d2').value);
        config.judge.max_tokens_d5      = parseInt(document.getElementById('judge-max-tokens-d5').value);
        config.judge.max_input_chars_d5 = parseInt(document.getElementById('judge-max-input-chars-d5').value);
        delete config.judge.max_tokens;

        // System Prompt
        config.system_prompt = document.getElementById('system-prompt').value;

        // Defenses
        config.defenses.d1_input_filter    = document.getElementById('d1').checked;
        config.defenses.d2_input_judge     = document.getElementById('d2').checked;
        config.defenses.d3_sp_lock         = document.getElementById('d3').checked;
        config.defenses.d4_sp_alignment    = document.getElementById('d4').checked;
        config.defenses.d5_output_judge    = document.getElementById('d5').checked;
        config.defenses.d6_output_sanitizer = document.getElementById('d6').checked;

        // RAG
        config.rag.enabled             = document.getElementById('rag-enabled').checked;
        config.rag.top_k               = parseInt(document.getElementById('rag-top-k').value);
        config.rag.distance_threshold  = parseFloat(document.getElementById('rag-distance-threshold').value);

        // RAG — Embedding
        config.rag.embedding = config.rag.embedding || {};
        config.rag.embedding.provider = document.getElementById('rag-embedding-provider').value;
        config.rag.embedding.model    = document.getElementById('rag-embedding-model').value;
        config.rag.embedding.base_url = document.getElementById('rag-embedding-base-url').value;
        config.rag.embedding.api_key  = document.getElementById('rag-embedding-api-key').value;
        config.rag.embedding.timeout  = parseInt(document.getElementById('rag-embedding-timeout').value);

        const res  = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config),
        });
        const body = await res.json().catch(() => ({}));

        let msg = t('toast.saved');
        if (body.invalidated && body.invalidated.includes('rag_index')) {
            msg += t('toast.rag_reindex');
        }
        if (body.invalidated && body.invalidated.includes('mcp_tools')) {
            msg += t('toast.mcp_reloaded');
        }
        if (body.needs_restart && body.needs_restart.length) {
            msg += t('toast.needs_restart') + body.needs_restart.join(', ');
        }
        showToast(msg);

    } catch (err) {
        showToast(t('toast.save_error') + err.message);
        console.error('saveConfig error:', err);
    }
}

function togglePassword(fieldId, btn) {
    const input = document.getElementById(fieldId);
    if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = '🔒';
    } else {
        input.type = 'password';
        btn.textContent = '👁';
    }
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}

document.getElementById('btn-save').addEventListener('click', saveConfig);

// ── Load config from file ──
const btnLoad = document.getElementById('btn-load');
const fileInput = document.getElementById('file-input');

btnLoad.addEventListener('click', () => {
    fileInput.value = '';
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
        showToast(t('toast.file_not_json'));
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        let parsed;
        try {
            parsed = JSON.parse(e.target.result);
        } catch (err) {
            showToast(t('toast.file_invalid_json') + err.message);
            return;
        }

        const errors = validateConfig(parsed);
        if (errors.length > 0) {
            showToast(t('toast.file_validation_error') + errors.join('; '));
            return;
        }

        config = parsed;
        applyConfigToForm(config);
        showToast(t('toast.file_loaded') + file.name);
    };
    reader.onerror = () => showToast(t('toast.file_read_error'));
    reader.readAsText(file);
});

function validateConfig(cfg) {
    const errors = [];
    if (typeof cfg !== 'object' || cfg === null) {
        errors.push(t('toast.val_not_object'));
        return errors;
    }

    // LLM
    if (!cfg.llm || typeof cfg.llm !== 'object') {
        errors.push(t('toast.val_missing_llm'));
    } else {
        if (!cfg.llm.provider) errors.push(t('toast.val_missing_field') + 'llm.provider');
        if (!cfg.llm.model) errors.push(t('toast.val_missing_field') + 'llm.model');
    }

    // Judge
    if (!cfg.judge || typeof cfg.judge !== 'object') {
        errors.push(t('toast.val_missing_judge'));
    } else {
        if (!cfg.judge.provider) errors.push(t('toast.val_missing_field') + 'judge.provider');
        if (!cfg.judge.model) errors.push(t('toast.val_missing_field') + 'judge.model');
    }

    // Defenses
    if (!cfg.defenses || typeof cfg.defenses !== 'object') {
        errors.push(t('toast.val_missing_defenses'));
    }

    // System prompt
    if (typeof cfg.system_prompt !== 'string') {
        errors.push(t('toast.val_missing_sp'));
    }

    // RAG
    if (!cfg.rag || typeof cfg.rag !== 'object') {
        errors.push(t('toast.val_missing_rag'));
    } else if (!cfg.rag.embedding || typeof cfg.rag.embedding !== 'object') {
        errors.push(t('toast.val_missing_field') + 'rag.embedding');
    }

    return errors;
}

async function reindexRAG() {
    const btn = document.getElementById('btn-reindex');
    btn.disabled = true;
    btn.textContent = t('toast.reindexing');
    try {
        const res  = await fetch('/api/admin/reindex-rag', { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
            showToast(t('toast.reindexed', { chunks: data.chunks }));
        } else {
            showToast(t('toast.load_error') + (data.error || t('toast.unknown_error')));
        }
    } catch (e) {
        showToast(t('toast.reindex_error'));
    } finally {
        btn.disabled = false;
        btn.textContent = t('admin.rag.reindex');
    }
}

document.getElementById('btn-reindex').addEventListener('click', reindexRAG);

loadConfig();
