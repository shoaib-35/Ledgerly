(function () {
    'use strict';

    // ---------- Sidebar collapse (desktop), persisted across visits ----------
    var shell = document.getElementById('app-shell');
    var toggle = document.getElementById('sidebar-toggle');
    if (shell && toggle) {
        if (localStorage.getItem('sidebar-collapsed') === '1') {
            shell.classList.add('sidebar-collapsed');
            toggle.setAttribute('aria-pressed', 'true');
        }
        toggle.addEventListener('click', function () {
            var collapsed = shell.classList.toggle('sidebar-collapsed');
            toggle.setAttribute('aria-pressed', String(collapsed));
            localStorage.setItem('sidebar-collapsed', collapsed ? '1' : '0');
        });
    }

    // ---------- Mobile "+" popup menu ----------
    var addButton = document.getElementById('mobile-add');
    var addMenu = document.getElementById('mobile-add-menu');
    var scrim = document.getElementById('scrim');
    function closeAddMenu() {
        if (!addMenu) return;
        addMenu.classList.remove('open');
        if (scrim) scrim.classList.remove('open');
        if (addButton) addButton.setAttribute('aria-expanded', 'false');
    }
    if (addButton && addMenu) {
        addButton.addEventListener('click', function (event) {
            event.stopPropagation();
            var isOpen = addMenu.classList.toggle('open');
            if (scrim) scrim.classList.toggle('open', isOpen);
            addButton.setAttribute('aria-expanded', String(isOpen));
        });
        document.addEventListener('click', function (event) {
            if (!addMenu.contains(event.target) && event.target !== addButton) closeAddMenu();
        });
        if (scrim) scrim.addEventListener('click', closeAddMenu);
    }

    // ---------- Add/Edit transaction form: only show the fields each type needs ----------
    var typeSelect = document.getElementById('tx-type');
    var accountSelect = document.getElementById('tx-account');
    if (typeSelect) {
        var CARD_PAYMENT = 'CARD_PAYMENT';
        var NO_PERSON_TYPES = ['CARD_PAYMENT', 'INCOME', 'BONUS', 'EXTRA'];

        function fieldEl(name) { return document.querySelector('[data-field="' + name + '"]'); }

        function refreshAccountOptions() {
            if (!accountSelect) return;
            var isCard = typeSelect.value === CARD_PAYMENT;
            Array.prototype.forEach.call(accountSelect.options, function (option) {
                if (!option.value) return;
                var accountType = option.getAttribute('data-account-type');
                var allowed = isCard ? accountType === 'CREDIT_CARD' : true;
                option.hidden = !allowed;
                if (!allowed && option.selected) option.selected = false;
            });
        }

        function syncFields() {
            var isCard = typeSelect.value === CARD_PAYMENT;
            var personField = fieldEl('person');
            var paymentSourceField = fieldEl('payment_source');
            var sourceAccountField = fieldEl('source_account');
            var accountField = fieldEl('account');

            if (personField) personField.classList.toggle('field-hidden', NO_PERSON_TYPES.indexOf(typeSelect.value) !== -1);
            if (paymentSourceField) paymentSourceField.classList.toggle('field-hidden', !isCard);
            if (sourceAccountField) sourceAccountField.classList.toggle('field-hidden', !isCard);

            if (accountField) {
                var normalLabel = accountField.getAttribute('data-label-normal') || 'Account';
                var cardLabel = accountField.getAttribute('data-label-card') || 'Credit card';
                var labelNode = accountField.childNodes[0];
                if (labelNode && labelNode.nodeType === Node.TEXT_NODE) {
                    labelNode.textContent = isCard ? cardLabel : normalLabel;
                }
            }
            refreshAccountOptions();
        }

        var paymentSourceSelect = document.getElementById('tx-payment-source');
        function syncSourceAccountVisibility() {
            var sourceAccountField = fieldEl('source_account');
            if (!sourceAccountField || !paymentSourceSelect) return;
            var isCard = typeSelect.value === CARD_PAYMENT;
            var isCash = paymentSourceSelect.value === 'CASH';
            sourceAccountField.classList.toggle('field-hidden', !isCard || isCash);
        }

        typeSelect.addEventListener('change', function () { syncFields(); syncSourceAccountVisibility(); });
        if (paymentSourceSelect) paymentSourceSelect.addEventListener('change', syncSourceAccountVisibility);
        syncFields();
        syncSourceAccountVisibility();
    }

    // ---------- Signup: password strength + confirmation match ----------
    var passwordInput = document.getElementById('password');
    var confirmInput = document.getElementById('password_confirm');
    if (passwordInput) {
        var fill = document.getElementById('strength-fill');
        var label = document.getElementById('strength-label');
        var COMMON = ['password', 'password1', '12345678', 'qwertyui', 'letmein', 'iloveyou', 'admin1234'];

        function scorePassword(value) {
            if (!value) return 0;
            var score = 0;
            if (value.length >= 8) score += 1;
            if (value.length >= 12) score += 1;
            if (/[a-z]/.test(value) && /[A-Z]/.test(value)) score += 1;
            if (/[0-9]/.test(value)) score += 1;
            if (/[^A-Za-z0-9]/.test(value)) score += 1;
            if (COMMON.indexOf(value.toLowerCase()) !== -1 || /^\d+$/.test(value)) score = Math.min(score, 1);
            return score;
        }

        function updateStrength() {
            var score = scorePassword(passwordInput.value);
            var pct = Math.min(score, 5) / 5 * 100;
            var colors = ['#bd684c', '#bd684c', '#d9a441', '#d9a441', '#1d6356', '#1d6356'];
            var labels = ['Enter a password', 'Very weak', 'Weak', 'Fair', 'Strong', 'Very strong'];
            if (fill) { fill.style.width = pct + '%'; fill.style.background = colors[score]; }
            if (label) label.textContent = passwordInput.value ? labels[score] : labels[0];
        }

        function updateMatch() {
            var hint = document.getElementById('password-match-hint');
            if (!hint || !confirmInput) return;
            if (!confirmInput.value) { hint.textContent = ''; return; }
            hint.textContent = confirmInput.value === passwordInput.value ? 'Passwords match.' : 'Passwords do not match.';
            hint.style.color = confirmInput.value === passwordInput.value ? 'var(--accent)' : 'var(--danger)';
        }

        passwordInput.addEventListener('input', function () { updateStrength(); updateMatch(); });
        if (confirmInput) confirmInput.addEventListener('input', updateMatch);
        updateStrength();
    }
})();
if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register(
            "/static/core/service-worker.js"
        );
    });
}