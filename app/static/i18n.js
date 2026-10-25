(function () {
    var LANG_KEY = 'pandora_lang';
    var LANGS = ['en', 'pt', 'es'];
    var FLAGS = {
        en: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40" width="20" height="14" style="vertical-align:-2px"><rect width="60" height="40" fill="#bf0a30"/><rect y="4" width="60" height="3.08" fill="#fff"/><rect y="10.16" width="60" height="3.08" fill="#fff"/><rect y="16.32" width="60" height="3.08" fill="#fff"/><rect y="22.48" width="60" height="3.08" fill="#fff"/><rect y="28.64" width="60" height="3.08" fill="#fff"/><rect y="34.80" width="60" height="3.08" fill="#fff"/><rect width="24" height="21.56" fill="#002868"/><g fill="#fff" font-size="2.5" text-anchor="middle"><text x="3" y="4">★</text><text x="9" y="4">★</text><text x="15" y="4">★</text><text x="21" y="4">★</text><text x="6" y="9">★</text><text x="12" y="9">★</text><text x="18" y="9">★</text><text x="3" y="14">★</text><text x="9" y="14">★</text><text x="15" y="14">★</text><text x="21" y="14">★</text></g></svg>',
        pt: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40" width="20" height="14" style="vertical-align:-2px"><rect width="60" height="40" fill="#009c3b"/><polygon points="30,4 56,20 30,36 4,20" fill="#ffdf00"/><circle cx="30" cy="20" r="8" fill="#002776"/><path d="M22 20 Q26 16 30 20 Q26 24 22 20 Z" fill="#fff" opacity="0.9"/></svg>',
        es: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40" width="20" height="14" style="vertical-align:-2px"><rect width="60" height="40" fill="#aa151b"/><rect y="10" width="60" height="20" fill="#f1bf00"/><rect y="30" width="60" height="10" fill="#aa151b"/></svg>'
    };
    var HTML_LANG = { en: 'en', pt: 'pt-BR', es: 'es' };
    var strings = {};
    var lang = 'en';

    try { lang = localStorage.getItem(LANG_KEY) || 'en'; } catch (e) {}
    if (LANGS.indexOf(lang) === -1) lang = 'en';

    function apply() {
        document.documentElement.lang = HTML_LANG[lang] || lang;

        document.querySelectorAll('[data-i18n]').forEach(function (el) {
            var s = strings[el.getAttribute('data-i18n')];
            if (s) el.textContent = s;
        });
        document.querySelectorAll('[data-i18n-html]').forEach(function (el) {
            var s = strings[el.getAttribute('data-i18n-html')];
            if (s) el.innerHTML = s;
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
            var s = strings[el.getAttribute('data-i18n-placeholder')];
            if (s) el.placeholder = s;
        });
        document.querySelectorAll('[data-i18n-title]').forEach(function (el) {
            var s = strings[el.getAttribute('data-i18n-title')];
            if (s) el.title = s;
        });

        var pageKey = document.body.getAttribute('data-page');
        if (pageKey && strings['title.' + pageKey]) {
            document.title = strings['title.' + pageKey];
        }

        document.querySelectorAll('[data-lang]').forEach(function (el) {
            el.style.display = el.getAttribute('data-lang') === lang ? '' : 'none';
        });

        var btn = document.getElementById('lang-toggle');
        if (btn) {
            var next = LANGS[(LANGS.indexOf(lang) + 1) % LANGS.length];
            btn.innerHTML = FLAGS[next];
            btn.title = next.toUpperCase();
        }
    }

    function load(newLang) {
        lang = newLang;
        try { localStorage.setItem(LANG_KEY, lang); } catch (e) {}
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/static/i18n/' + lang + '.json', true);
        xhr.onload = function () {
            if (xhr.status === 200) {
                strings = JSON.parse(xhr.responseText);
                apply();
                window._i18nReady = true;
                window.dispatchEvent(new Event('i18n-ready'));
            }
        };
        xhr.send();
    }

    window.t = function (key, replacements) {
        var s = strings[key] || key;
        if (replacements) {
            Object.keys(replacements).forEach(function (k) {
                s = s.replace('{' + k + '}', replacements[k]);
            });
        }
        return s;
    };

    window.getLang = function () { return lang; };

    window.toggleLang = function () {
        var next = LANGS[(LANGS.indexOf(lang) + 1) % LANGS.length];
        load(next);
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { load(lang); });
    } else {
        load(lang);
    }
})();
