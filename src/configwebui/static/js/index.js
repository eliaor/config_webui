'use strict';

let editor;
let editor_is_ready = false;
let isAdmin = false;

const pageRefreshDelay = 400;
const statusIconDisappearDelay = 800;

const navbarMenu = document.querySelector("#navbar-menu");
const adminGuestUi = document.querySelector('#admin-guest-ui');
const adminAuthUi = document.querySelector('#admin-auth-ui');
const adminLoginBtn = document.querySelector('#admin-login-btn');
const adminLogoutBtn = document.querySelector('#admin-logout-btn');
const adminLoginModalElement = document.querySelector('#adminLoginModal');
const adminLoginForm = document.querySelector('#admin-login-form');
const adminPasswordInput = document.querySelector('#admin-password-input');
const adminLoginError = document.querySelector('#admin-login-error');
const adminLoginSubmitBtn = document.querySelector('#admin-login-submit-btn');

const presetSelect = document.querySelector('#preset-select');
const applyPresetBtn = document.querySelector('#apply-preset-btn');

const saveActionButtons = document.querySelectorAll('.save-action');
const terminateActionButtons = document.querySelectorAll('.terminate-action');

const flashMessagesContent = document.querySelector('#flash-messages-content');

const configFormLoadingIcon = document.querySelector('#config-form-loading-icon');
const configFormContent = document.querySelector('#config-form-content');
const configFormEdit = document.querySelector('#config-form-edit');
const configFormContentPlaceholder = document.querySelector('#config-form-content-placeholder');

function showLoadingIcon(colorClass = 'text-primary') {
    if (configFormLoadingIcon) {
        configFormLoadingIcon.className = `spinner-border ${colorClass}`;
        configFormLoadingIcon.style.display = 'inline-block';
    }
}

function hideLoadingIcon() {
    if (configFormLoadingIcon) {
        configFormLoadingIcon.style.display = 'none';
    }
}

const jsonCodeExpandButton = document.querySelector('#json-code-expand');
const jsonCodeCollapseButton = document.querySelector('#json-code-collapse');
const jsonCodeContent = document.querySelector('#json-code-content');
const jsonCodeEdit = document.querySelector('#json-code-edit');
const jsonCodeContentPlaceholder = document.querySelector('#json-code-content-placeholder');
const jsonCodeContentPlaceholderLabel = jsonCodeContentPlaceholder ? jsonCodeContentPlaceholder.querySelector('button > span') : null;

let bsAdminLoginModal = null;
if (adminLoginModalElement && typeof bootstrap !== 'undefined') {
    bsAdminLoginModal = new bootstrap.Modal(adminLoginModalElement);
}

const bsCollapseNavbarMenu = navbarMenu ? new bootstrap.Collapse(navbarMenu, { toggle: false }) : null;
const bsCollapseConfigFormContent = configFormContent ? new bootstrap.Collapse(configFormContent, { toggle: false }) : null;
const bsCollapseConfigFormContentPlaceHolder = configFormContentPlaceholder ? new bootstrap.Collapse(configFormContentPlaceholder, { toggle: false }) : null;
const bsCollapsejsonCodeContent = jsonCodeContent ? new bootstrap.Collapse(jsonCodeContent, { toggle: false }) : null;
const bsCollapsejsonCodeContentPlaceholder = jsonCodeContentPlaceholder ? new bootstrap.Collapse(jsonCodeContentPlaceholder, { toggle: false }) : null;

function focusElementFromHash() {
    const hash = window.location.hash;
    if (hash) {
        const target = document.querySelector(hash);
        if (target) {
            target.focus();
        }
    }
}

function collapseNavbar() {
    if (bsCollapseNavbarMenu) {
        bsCollapseNavbarMenu.hide();
    }
}

function flashMessage(message, category, scroll = true) {
    const iconClass = {
        'info': 'fas fa-info-circle',
        'success': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-triangle',
        'danger': 'fas fa-times-circle'
    };
    const icon = iconClass[category] || iconClass['info'];
    const messageHTML = `
        <div class="alert alert-${category} alert-dismissible fade show" role="alert">
            <div>
                <span><i class="${icon}"></i></span>
                <span>${message}</span>
            </div>
            <button class="btn-close" type="button" title="Dismiss" data-bs-dismiss="alert" aria-label="Dismiss"></button>
        </div>
    `;
    if (flashMessagesContent) {
        flashMessagesContent.insertAdjacentHTML('beforeend', messageHTML);
    }
    if (scroll) {
        window.scroll({
            top: 0,
            behavior: 'smooth'
        });
    }
    return messageHTML;
}

function clearFlashMessage() {
    if (flashMessagesContent) {
        flashMessagesContent.innerHTML = '';
    }
}

async function getConfigAndSchema() {
    let res = {};
    try {
        const response = await fetch('/api/config', { method: 'GET' });
        const data = await response.json();
        res.config = data.config;
        res.schema = data.schema;
        res.is_admin = data.is_admin;
        res.presets = data.presets;
        if (!data.success) {
            flashMessage('Failed to get config from server.', 'danger');
        }
    } catch (error) {
        flashMessage('Failed to get config from server.', 'danger');
    }
    return res;
}

function updateAdminUI(adminStatus) {
    isAdmin = adminStatus;
    if (adminGuestUi && adminAuthUi) {
        if (isAdmin) {
            adminGuestUi.style.setProperty('display', 'none', 'important');
            adminAuthUi.style.removeProperty('display');
            adminAuthUi.style.display = 'flex';
        } else {
            adminAuthUi.style.setProperty('display', 'none', 'important');
            adminGuestUi.style.removeProperty('display');
            adminGuestUi.style.display = 'flex';
        }
    }
}

function hasPasswordFormat(schema) {
    if (typeof schema !== "object" || schema === null) {
        return false;
    }
    if (schema.format === "password") {
        return true;
    }
    if (schema.properties) {
        for (const key in schema.properties) {
            if (hasPasswordFormat(schema.properties[key])) {
                return true;
            }
        }
    }
    if (schema.items) {
        if (Array.isArray(schema.items)) {
            for (const item of schema.items) {
                if (hasPasswordFormat(item)) {
                    return true;
                }
            }
        } else if (hasPasswordFormat(schema.items)) {
            return true;
        }
    }
    if (schema.anyOf || schema.oneOf || schema.allOf) {
        const schemas = schema.anyOf || schema.oneOf || schema.allOf;
        for (const subSchema of schemas) {
            if (hasPasswordFormat(subSchema)) {
                return true;
            }
        }
    }
    return false;
}

function changeCheckboxStyle() {
    if (!configFormEdit) return;
    const checkboxes = configFormEdit.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(input => {
        if (input.parentElement.tagName.toLowerCase() === 'span' && input.parentElement.attributes.length === 0) {
            const parentSpan = input.parentElement;
            const parentOfParent = parentSpan.parentElement;
            while (parentSpan.firstChild) {
                parentOfParent.insertBefore(parentSpan.firstChild, parentSpan);
            }
            parentSpan.remove();
        }

        const parent = input.parentElement;
        const newLabel = document.createElement('label');
        newLabel.setAttribute('for', input.id);

        parent.removeAttribute('for');
        if (parent.classList.contains('editor-check') || parent.classList.contains('check-list')) {
            return;
        }

        input.className += ' form-check-input editor-check-input';
        if (parent.tagName.toLowerCase() === 'label') {
            input.className += ' form-check-input editor-check-input check-input-plain';
            parent.className = 'form-check editor-check';
            newLabel.className = 'form-check-label check-label-plain';
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'span') {
            input.className += ' form-check-input editor-check-input check-input-heading';
            parent.className = 'form-check editor-check d-inline-flex';
            newLabel.className = 'form-check-label check-label-heading';

            parent.childNodes.forEach(child => {
                if (child.nodeType === Node.TEXT_NODE && child.textContent.trim() !== '') {
                    newLabel.appendChild(child);
                }
            });
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'b') {
            input.className += ' form-check-input editor-check-input check-input-plain';
            parent.className = 'form-check editor-check user-add-item';
            newLabel.className = 'form-check-label check-label-plain';

            parent.insertBefore(newLabel, input.nextSibling);

            const newParent = document.createElement('label');
            while (parent.firstChild) {
                newParent.appendChild(parent.firstChild);
            }
            Array.from(parent.attributes).forEach(attr => {
                newParent.setAttribute(attr.name, attr.value);
            });
            parent.replaceWith(newParent);
        } else if (parent.tagName.toLowerCase() === 'div') {
            parent.className += ' check-list';
            const formLabelElement = parent.querySelector('label[class="form-check-label"]');
            if (formLabelElement) {
                formLabelElement.textContent = formLabelElement.textContent.trim();
            }
            const newParent = document.createElement('label');
            while (parent.firstChild) {
                newParent.appendChild(parent.firstChild);
            }
            Array.from(parent.attributes).forEach(attr => {
                newParent.setAttribute(attr.name, attr.value);
            });
            parent.replaceWith(newParent);
        }
    });
}

function changeButtonGroupStyle() {
    const buttonGroups = document.querySelectorAll('span.btn-group');
    buttonGroups.forEach(buttonGroup => {
        if (buttonGroup.style.display === 'inline-block') {
            buttonGroup.removeAttribute('style');
        }
        if (buttonGroup.querySelector('button.json-editor-btntype-delete') !== null) {
            buttonGroup.classList.add('mb-1');
        }
    });
}

function setAnchor() {
    document.querySelectorAll('[data-schemapath]').forEach(element => {
        if (!element.id) {
            const dataSchemaPath = element.getAttribute('data-schemapath');
            const parts = dataSchemaPath.split('.');
            const anchor = parts.map((part, index) => {
                return index >= 1 ? `[${part}]` : part;
            }).join('');
            if (!document.getElementById(anchor)) {
                element.id = anchor;
            }
        }
    });
}

function changeStyle() {
    changeCheckboxStyle();
    changeButtonGroupStyle();
    setAnchor();
}

function showConfigFormContent() {
    if (bsCollapseConfigFormContent) {
        setTimeout(() => { bsCollapseConfigFormContent.show(); }, 0);
    }
    if (bsCollapseConfigFormContentPlaceHolder) {
        setTimeout(() => { bsCollapseConfigFormContentPlaceHolder.hide(); }, 0);
    }
}

function toggleJsonCodeContent(action) {
    if (action === 'show') {
        if (bsCollapsejsonCodeContent) bsCollapsejsonCodeContent.show();
        if (bsCollapsejsonCodeContentPlaceholder) bsCollapsejsonCodeContentPlaceholder.hide();
        if (jsonCodeExpandButton) jsonCodeExpandButton.style.display = 'none';
        if (jsonCodeCollapseButton) jsonCodeCollapseButton.style.removeProperty('display');
    } else if (action === 'hide') {
        if (bsCollapsejsonCodeContent) bsCollapsejsonCodeContent.hide();
        if (bsCollapsejsonCodeContentPlaceholder) bsCollapsejsonCodeContentPlaceholder.show();
        if (jsonCodeExpandButton) jsonCodeExpandButton.style.removeProperty('display');
        if (jsonCodeCollapseButton) jsonCodeCollapseButton.style.display = 'none';
    }
}

async function initializeConfigFormEditor(keepValues = false) {
    showLoadingIcon('text-primary');

    const currentValues = (keepValues && editor) ? editor.getValue() : null;

    const data = await getConfigAndSchema();
    const myschema = data.schema || {};
    const myconfig = currentValues || data.config || {};
    updateAdminUI(data.is_admin);

    if (data.presets && presetSelect) {
        const currentSelected = presetSelect.value;
        presetSelect.innerHTML = '';
        data.presets.forEach(p => {
            const option = document.createElement('option');
            option.value = p;
            option.textContent = p;
            if (p === currentSelected) option.selected = true;
            presetSelect.appendChild(option);
        });
    }

    if (editor) {
        editor.destroy();
    }

    const jsonEditorConfig = {
        form_name_root: 'config',
        iconlib: 'fontawesome5',
        theme: 'bootstrap5',
        show_opt_in: false,
        disable_edit_json: true,
        disable_properties: true,
        disable_collapse: false,
        enable_array_copy: true,
        no_additional_properties: true,
        enforce_const: true,
        startval: myconfig,
        schema: myschema
    };

    editor = new JSONEditor(configFormEdit, jsonEditorConfig);

    editor.on('change', function () {
        if (editor_is_ready) {
            setTimeout(() => changeStyle(), 0);
            if (jsonCodeEdit) {
                try {
                    jsonCodeEdit.value = JSON.stringify(editor.getValue(), null, 4);
                } catch (e) {}
            }
        }
    });

    function onEditorReady() {
        editor_is_ready = true;
        try {
            changeStyle();
        } catch (e) {
            console.error('Error applying styles:', e);
        }
        showConfigFormContent();
        if (hasPasswordFormat(myschema)) {
            if (jsonCodeContentPlaceholderLabel) {
                jsonCodeContentPlaceholderLabel.textContent = 'Expanding JSON may expose sensitive information.';
            }
            if (jsonCodeExpandButton) {
                jsonCodeExpandButton.className = 'btn btn-outline-danger';
            }
        } else {
            toggleJsonCodeContent('show');
        }
        if (jsonCodeEdit) {
            try {
                jsonCodeEdit.value = JSON.stringify(editor.getValue(), null, 4);
                jsonCodeEdit.wrap = "off";
            } catch (e) {}
        }
        setTimeout(hideLoadingIcon, 100);
    }

    editor.on('ready', onEditorReady);
    if (editor.ready) {
        onEditorReady();
    }
    // Safety fallback: ensure loading icon is hidden
    setTimeout(hideLoadingIcon, 600);
}

async function saveConfig() {
    clearFlashMessage();
    if (!editor) return;

    const errors = editor.validate();
    if (errors.length) {
        errors.forEach(error => {
            const parts = error.path.split('.');
            const href = parts.map((part, index) => {
                return index >= 1 ? `[${part}]` : part;
            }).join('');
            flashMessage(`Property "<b>${error.property}</b>" unsatisfied at {<a href="#${href}" class="alert-link">${error.path}</a>}: ${error.message}`, 'danger');
        });
        return;
    }

    const configValue = editor.getValue();
    try {
        const response = await fetch('/api/config', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config: configValue })
        });
        const data = await response.json();
        const category = data.success ? 'success' : 'danger';
        for (const message of data.messages) {
            flashMessage(message, category);
        }
        return data.success;
    } catch (error) {
        flashMessage('Failed to save configuration. Is the backend service running?', 'danger');
        return false;
    }
}

async function applySelectedPreset() {
    clearFlashMessage();
    if (!presetSelect) return;
    const selectedPreset = presetSelect.value;
    if (!selectedPreset) {
        flashMessage('No preset selected.', 'warning');
        return;
    }

    showLoadingIcon('text-primary');

    try {
        const applyResponse = await fetch(`/api/presets/${encodeURIComponent(selectedPreset)}/apply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ save: true })
        });
        const applyData = await applyResponse.json();
        if (!applyData.success) {
            hideLoadingIcon();
            flashMessage(`Failed to apply preset "${selectedPreset}": ${(applyData.messages || []).join(' ')}`, 'danger');
            return;
        }

        await initializeConfigFormEditor(false);

        flashMessage(
            `Preset "<strong>${selectedPreset}</strong>" applied and saved. ` +
            `Click <strong>Save</strong> again to overwrite with any further edits.`,
            'success'
        );
    } catch (error) {
        hideLoadingIcon();
        flashMessage('Failed to apply preset from server.', 'danger');
    }
}

async function adminLogin() {
    const password = adminPasswordInput.value;
    if (!password) {
        if (adminLoginError) {
            adminLoginError.textContent = 'Password is required.';
            adminLoginError.classList.remove('d-none');
        }
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: password })
        });
        const data = await response.json();
        if (data.success) {
            if (adminLoginError) {
                adminLoginError.classList.add('d-none');
            }
            adminPasswordInput.value = '';
            if (bsAdminLoginModal) {
                bsAdminLoginModal.hide();
            }
            flashMessage('Logged in as Admin. All read-only fields are now editable.', 'success');
            await initializeConfigFormEditor(true);
        } else {
            if (adminLoginError) {
                adminLoginError.textContent = data.messages && data.messages.length ? data.messages[0] : 'Invalid admin password.';
                adminLoginError.classList.remove('d-none');
            }
        }
    } catch (error) {
        if (adminLoginError) {
            adminLoginError.textContent = 'Error connecting to authentication server.';
            adminLoginError.classList.remove('d-none');
        }
    }
}

async function adminLogout() {
    clearFlashMessage();
    try {
        const response = await fetch('/api/logout', { method: 'POST' });
        const data = await response.json();
        flashMessage(data.messages[0] || 'Logged out from admin mode.', 'info');
        await initializeConfigFormEditor(true);
    } catch (error) {
        flashMessage('Failed to logout from admin mode.', 'danger');
    }
}

async function terminate() {
    clearFlashMessage();
    try {
        flashMessage('Shutting down the editor backend. Subsequent changes will not be saved.', 'warning');
        await fetch(`/api/shutdown`, { method: 'GET' });
    } catch (error) {
        flashMessage('Failed to shut down the editor backend. It may already be stopped.', 'danger');
    }
}

// Event Listeners
saveActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        await saveConfig();
    });
});

if (presetSelect) {
    presetSelect.addEventListener('change', async () => {
        await applySelectedPreset();
    });
}

if (applyPresetBtn) {
    applyPresetBtn.addEventListener('click', async () => {
        await applySelectedPreset();
    });
}

if (adminLoginSubmitBtn) {
    adminLoginSubmitBtn.addEventListener('click', async () => {
        await adminLogin();
    });
}

if (adminPasswordInput) {
    adminPasswordInput.addEventListener('keypress', async (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            await adminLogin();
        }
    });
}

if (adminLogoutBtn) {
    adminLogoutBtn.addEventListener('click', async () => {
        await adminLogout();
    });
}

terminateActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        await terminate();
    });
});

if (jsonCodeExpandButton) {
    jsonCodeExpandButton.addEventListener('click', () => {
        toggleJsonCodeContent('show');
    });
}

if (jsonCodeCollapseButton) {
    jsonCodeCollapseButton.addEventListener('click', () => {
        toggleJsonCodeContent('hide');
    });
}

window.addEventListener("DOMContentLoaded", focusElementFromHash);
window.addEventListener("hashchange", focusElementFromHash);

// Start
initializeConfigFormEditor();