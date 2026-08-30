'use strict';

let editor;
let editor_is_ready = false;
let isAdmin = false;
let fetchingTerminalOutput = false;
let pendingClearTerminalOutput = false;

const pageRefreshDelay = 400;
const statusIconDisappearDelay = 400;
const terminalOutputDisplayRefreshDelay = 200;

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
const resetActionButtons = document.querySelectorAll('.reset-action');
const launchActionButtons = document.querySelectorAll('.launch-action');
const terminateActionButtons = document.querySelectorAll('.terminate-action');

const flashMessagesContent = document.querySelector('#flash-messages-content');

const configFormLoadingIcon = document.querySelector('#config-form-loading-icon');
const configFormLoadingIconBaseClassName = configFormLoadingIcon ? configFormLoadingIcon.className : '';
const configFormContent = document.querySelector('#config-form-content');
const configFormEdit = document.querySelector('#config-form-edit');
const configFormContentPlaceholder = document.querySelector('#config-form-content-placeholder');

const jsonCodeExpandButton = document.querySelector('#json-code-expand');
const jsonCodeCollapseButton = document.querySelector('#json-code-collapse');
const jsonCodeContent = document.querySelector('#json-code-content');
const jsonCodeEdit = document.querySelector('#json-code-edit');
const jsonCodeContentPlaceholder = document.querySelector('#json-code-content-placeholder');
const jsonCodeContentPlaceholderLabel = jsonCodeContentPlaceholder ? jsonCodeContentPlaceholder.querySelector('button > span') : null;

const terminalOutputHeading = document.querySelector('#terminal-output-heading');
const mainProgramRunningIcon = document.querySelector('#main-program-running-icon');
const mainProgramRunningIconBaseClassName = mainProgramRunningIcon ? mainProgramRunningIcon.className : '';
const terminalOutputRefreshButton = document.querySelector('#terminal-output-refresh');
const terminalOutputClearButton = document.querySelector('#terminal-output-clear');
const terminalOutputDisplay = document.querySelector('#terminal-output-display');
const terminalOutputDisplayBaseClassName = terminalOutputDisplay ? terminalOutputDisplay.className : '';

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
        if (data.success) {
            if (configFormLoadingIcon) {
                configFormLoadingIcon.className = configFormLoadingIconBaseClassName + ' text-success';
            }
        } else {
            if (configFormLoadingIcon) {
                configFormLoadingIcon.className = configFormLoadingIconBaseClassName + ' text-danger';
            }
            flashMessage('Failed to get config from server.', 'danger');
        }
    } catch (error) {
        flashMessage('Failed to get config from server.', 'danger');
        if (configFormLoadingIcon) {
            configFormLoadingIcon.className = configFormLoadingIconBaseClassName + ' text-danger';
        }
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
    if (configFormLoadingIcon) {
        configFormLoadingIcon.className = configFormLoadingIconBaseClassName + ' text-primary';
        configFormLoadingIcon.style.display = 'inline-block';
    }

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
        show_opt_in: true,
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
                jsonCodeEdit.value = JSON.stringify(editor.getValue(), null, 4);
            }
        }
    });

    editor.on('ready', function () {
        editor_is_ready = true;
        setTimeout(() => { changeStyle(); }, 0);
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
            jsonCodeEdit.value = JSON.stringify(editor.getValue(), null, 4);
            jsonCodeEdit.wrap = "off";
        }
        if (configFormLoadingIcon) {
            setTimeout(() => { configFormLoadingIcon.style.display = 'none'; }, statusIconDisappearDelay);
        }
    });
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

async function resetConfig() {
    clearFlashMessage();
    try {
        const response = await fetch('/api/reset', { method: 'POST' });
        const data = await response.json();
        if (data.success && editor) {
            editor.setValue(data.config);
            setTimeout(() => changeStyle(), 0);
            if (jsonCodeEdit) {
                jsonCodeEdit.value = JSON.stringify(data.config, null, 4);
            }
            flashMessage('Configuration reset to saved state.', 'info');
        }
    } catch (error) {
        flashMessage('Failed to reset configuration.', 'danger');
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

    try {
        const response = await fetch(`/api/presets/${encodeURIComponent(selectedPreset)}`, {
            method: 'GET'
        });
        const data = await response.json();
        if (data.success && editor) {
            editor.setValue(data.config);
            setTimeout(() => changeStyle(), 0);
            if (jsonCodeEdit) {
                jsonCodeEdit.value = JSON.stringify(data.config, null, 4);
            }
            flashMessage(`Loaded preset "<strong>${selectedPreset}</strong>". Click <strong>Save</strong> to persist to config file.`, 'info');
        } else {
            flashMessage(`Failed to load preset "${selectedPreset}".`, 'danger');
        }
    } catch (error) {
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

async function launch() {
    clearFlashMessage();
    try {
        const response = await fetch(`/api/launch`, { method: 'GET' });
        const data = await response.json();
        const messageCategory = (data.success ? 'success' : 'danger');
        const scroll = !data.success;
        for (const message of data.messages) {
            flashMessage(message, messageCategory, scroll);
        }
        if (!scroll && terminalOutputHeading && terminalOutputDisplay) {
            terminalOutputHeading.scrollIntoView({ behavior: "smooth" });
            terminalOutputDisplay.focus();
        }
        return data.success;
    } catch (error) {
        flashMessage('Failed to launch the main program. Check your backend.', 'danger');
        return false;
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

function processCarriageReturn(input) {
    const lines = input.split('\n');
    const processedLines = lines.map(line => {
        const parts = line.split('\r');
        let result = '';
        for (let i = parts.length - 1; i >= 0; i--) {
            result = result + parts[i].substring(result.length);
        }
        return result;
    });
    return processedLines.join('\n');
}

async function clearTerminalOutput() {
    await fetch("/api/clear_terminal_output", { method: 'POST' });
    pendingClearTerminalOutput = true;
    if (terminalOutputDisplay) {
        terminalOutputDisplay.value = '';
        terminalOutputDisplay.wrap = "on";
        terminalOutputDisplay.className = terminalOutputDisplayBaseClassName;
    }
}

function getTerminalOutput(recentOnly) {
    if (fetchingTerminalOutput) {
        return;
    }
    let lastRequestComplete = true;
    const url = "/api/get_terminal_output";
    const err_message = 'Failed to get output from the main program.';
    if (!recentOnly && terminalOutputDisplay) {
        terminalOutputDisplay.value = '';
    }
    let textSinceLastLine = '';
    let textUntilLastLine = terminalOutputDisplay ? terminalOutputDisplay.value : '';
    if (terminalOutputDisplay) {
        terminalOutputDisplay.className = terminalOutputDisplayBaseClassName;
        terminalOutputDisplay.scrollTop = terminalOutputDisplay.scrollHeight;
    }

    if (mainProgramRunningIcon) {
        mainProgramRunningIcon.className = mainProgramRunningIconBaseClassName + ' text-primary';
    }

    const intervalId = setInterval(async () => {
        if (!lastRequestComplete) {
            return;
        }
        if (mainProgramRunningIcon) {
            mainProgramRunningIcon.style.display = 'inline-block';
        }
        try {
            lastRequestComplete = false;
            if (pendingClearTerminalOutput && terminalOutputDisplay) {
                terminalOutputDisplay.value = '';
                terminalOutputDisplay.wrap = "on";
                textSinceLastLine = '';
                textUntilLastLine = '';
                pendingClearTerminalOutput = false;
            }
            const currentURL = url + '?recent_only=' + (recentOnly ? '1' : '0');

            const response = await fetch(currentURL, { method: 'GET' });
            const data = await response.json();
            recentOnly = true;
            let scroll = false;
            if (terminalOutputDisplay && terminalOutputDisplay.scrollTop + terminalOutputDisplay.clientHeight >= terminalOutputDisplay.scrollHeight - 10) {
                scroll = true;
            }

            const terminalText = textSinceLastLine + data.combined_output;
            const lastNewlineIndex = terminalText.lastIndexOf('\n');
            if (lastNewlineIndex !== -1) {
                textUntilLastLine += processCarriageReturn(terminalText.substring(0, lastNewlineIndex + 1));
                textSinceLastLine = terminalText.substring(lastNewlineIndex + 1);
            } else {
                textSinceLastLine = terminalText;
            }

            if (terminalOutputDisplay) {
                terminalOutputDisplay.wrap = "off";
                terminalOutputDisplay.value = textUntilLastLine + processCarriageReturn(textSinceLastLine);
            }

            if (data.has_warning) {
                if (mainProgramRunningIcon) mainProgramRunningIcon.className = mainProgramRunningIconBaseClassName + ' text-warning';
                if (terminalOutputDisplay) terminalOutputDisplay.className = terminalOutputDisplayBaseClassName + ' text-warning';
            }
            if (!data.running) {
                if (data.state) {
                    if (!data.has_warning) {
                        if (terminalOutputDisplay) terminalOutputDisplay.className = terminalOutputDisplayBaseClassName + ' text-success';
                        if (mainProgramRunningIcon) mainProgramRunningIcon.className = mainProgramRunningIconBaseClassName + ' text-success';
                    }
                } else {
                    if (terminalOutputDisplay) terminalOutputDisplay.className = terminalOutputDisplayBaseClassName + ' text-danger';
                    if (mainProgramRunningIcon) mainProgramRunningIcon.className = mainProgramRunningIconBaseClassName + ' text-danger';
                }
                for (const message of data.messages) {
                    if (terminalOutputDisplay) terminalOutputDisplay.value += '\n' + message + '\n';
                }
                if (mainProgramRunningIcon) {
                    setTimeout(() => { mainProgramRunningIcon.style.display = 'none'; }, statusIconDisappearDelay);
                }
                fetchingTerminalOutput = false;
                clearInterval(intervalId);
            }
            if (scroll && terminalOutputDisplay) {
                terminalOutputDisplay.scrollTop = terminalOutputDisplay.scrollHeight;
            }
        } catch (error) {
            if (terminalOutputDisplay) terminalOutputDisplay.className = terminalOutputDisplayBaseClassName + ' text-danger';
            if (mainProgramRunningIcon) mainProgramRunningIcon.className = mainProgramRunningIconBaseClassName + ' text-danger';
            flashMessage(err_message, 'danger');
            if (mainProgramRunningIcon) {
                setTimeout(() => { mainProgramRunningIcon.style.display = 'none'; }, statusIconDisappearDelay);
            }
            fetchingTerminalOutput = false;
            clearInterval(intervalId);
        }
        lastRequestComplete = true;
    }, terminalOutputDisplayRefreshDelay);
    fetchingTerminalOutput = true;
}

// Event Listeners
saveActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        await saveConfig();
    });
});

resetActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        await resetConfig();
    });
});

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

launchActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        if (await launch()) {
            getTerminalOutput(true);
        }
    });
});

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

if (terminalOutputRefreshButton) {
    terminalOutputRefreshButton.addEventListener('click', () => {
        getTerminalOutput(false);
    });
}

if (terminalOutputClearButton) {
    terminalOutputClearButton.addEventListener('click', () => {
        clearTerminalOutput();
    });
}

window.addEventListener("DOMContentLoaded", focusElementFromHash);
window.addEventListener("hashchange", focusElementFromHash);

// Start
initializeConfigFormEditor();