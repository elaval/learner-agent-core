// i18n - Internationalization Module

class I18n {
    constructor() {
        this.currentLanguage = localStorage.getItem('ui_language') || 'en';
        this.translations = {};
        this.fallbackLanguage = 'en';
    }

    async loadLanguage(lang) {
        try {
            const response = await fetch(`/static/i18n/${lang}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load ${lang}.json`);
            }
            this.translations[lang] = await response.json();
            return true;
        } catch (error) {
            console.error(`Error loading language ${lang}:`, error);
            return false;
        }
    }

    async init() {
        // Load both languages
        await Promise.all([
            this.loadLanguage('en'),
            this.loadLanguage('es')
        ]);

        // Set current language
        await this.setLanguage(this.currentLanguage);
    }

    async setLanguage(lang) {
        if (!this.translations[lang]) {
            await this.loadLanguage(lang);
        }

        this.currentLanguage = lang;
        localStorage.setItem('ui_language', lang);

        // Update HTML lang attribute
        document.documentElement.lang = lang;

        // Update all translatable elements
        this.updatePageTranslations();

        // Update language selector if it exists
        const selector = document.getElementById('ui-language-select');
        if (selector) {
            selector.value = lang;
        }
    }

    t(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations[this.currentLanguage];

        // Navigate through nested keys
        for (const k of keys) {
            if (value && typeof value === 'object') {
                value = value[k];
            } else {
                // Fallback to English
                value = this.translations[this.fallbackLanguage];
                for (const fk of keys) {
                    if (value && typeof value === 'object') {
                        value = value[fk];
                    } else {
                        return key; // Return key if not found
                    }
                }
                break;
            }
        }

        // Replace parameters
        if (typeof value === 'string' && Object.keys(params).length > 0) {
            return value.replace(/\{(\w+)\}/g, (match, paramKey) => {
                return params[paramKey] !== undefined ? params[paramKey] : match;
            });
        }

        return value || key;
    }

    updatePageTranslations() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            element.textContent = this.t(key);
        });

        // Update all elements with data-i18n-placeholder attribute
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });

        // Update all elements with data-i18n-html attribute (for HTML content)
        document.querySelectorAll('[data-i18n-html]').forEach(element => {
            const key = element.getAttribute('data-i18n-html');
            element.innerHTML = this.t(key);
        });
    }

    async changeLanguage(lang) {
        await this.setLanguage(lang);
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }
}

// Global i18n instance
const i18n = new I18n();
