(function(){
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    function createButton() {
        const titleEl = document.querySelector('#id_title');
        if (!titleEl) return;
        // avoid adding twice
        if (document.querySelector('#autofill-scheme-button')) return;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.id = 'autofill-scheme-button';
        btn.className = 'button';
        btn.style.marginLeft = '8px';
        btn.textContent = 'Autofill from Gemini';
        btn.addEventListener('click', onClick);
        // place after title input
        titleEl.parentNode.appendChild(btn);
    }

    async function onClick(e) {
        const btn = e.currentTarget;
        const title = (document.querySelector('#id_title') || {}).value || '';
        if (!title.trim()) {
            alert('Please enter a title first');
            return;
        }
        btn.disabled = true;
        const prevText = btn.textContent;
        btn.textContent = 'Autofilling...';
        try {
                // Construct the admin-model base path (e.g. /admin/chatbot/governmentscheme/)
                // Remove trailing 'add/' or '<pk>/change/' from the current pathname if present.
                let basePath = window.location.pathname.replace(/(add\/|\d+\/change\/?$)/, '');
                if (!basePath.endsWith('/')) basePath += '/';
                const url = basePath + 'autofill/';
            const csrftoken = getCookie('csrftoken') || getCookie('CSRF_COOKIE') || '';
            const resp = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                    'Accept': 'application/json'
                },
                body: JSON.stringify({title: title, language: (document.querySelector('#id_language')||{}).value || 'en'})
            });
            if (!resp.ok) {
                const txt = await resp.text();
                alert('Autofill failed: ' + resp.status + '\n' + txt);
                return;
            }
            const data = await resp.json();
            if (!data.ok) {
                alert('Autofill error: ' + (data.error || 'unknown'));
                return;
            }
            applyDataToForm(data.data || {});
            btn.textContent = 'Autofilled ✓';
            setTimeout(()=> btn.textContent = prevText, 2000);
        } catch (err) {
            alert('Autofill request failed: ' + err.message);
        } finally {
            btn.disabled = false;
        }
    }

    function applyDataToForm(d) {
        const setVal = (id, val) => {
            const el = document.querySelector('#id_' + id);
            if (!el) return;
            if (el.tagName === 'SELECT') {
                // try to match option by value or text
                const v = String(val || '');
                // try exact value
                let found = false;
                for (let i=0;i<el.options.length;i++){
                    const opt = el.options[i];
                    if (opt.value === v) { el.value = v; found = true; break; }
                    if ((opt.text || '').trim().toLowerCase() === v.trim().toLowerCase()) { el.value = opt.value; found = true; break; }
                }
                if (!found && v) {
                    // leave as-is
                }
                return;
            }
            if (el.type === 'checkbox') {
                el.checked = !!val;
                return;
            }
            if (el.tagName === 'TEXTAREA') {
                if (Array.isArray(val) || typeof val === 'object') {
                    el.value = JSON.stringify(val, null, 2);
                } else {
                    el.value = String(val || '');
                }
                return;
            }
            el.value = val === null || val === undefined ? '' : String(val);
        };

        // Common fields mapping
        const mapping = [
            'description','short_description','ministry','department','government_level','state','eligibility_criteria',
            'benefits','financial_assistance','application_process','application_link','launch_date','last_date',
            'validity_period','helpline_number','email','website','source_url'
        ];
        mapping.forEach(k => {
            if (k in d) setVal(k, d[k]);
        });
        // JSON fields
        if ('required_documents' in d) setVal('required_documents', d['required_documents']);
        if ('keywords' in d) setVal('keywords', d['keywords']);
        if ('search_tags' in d) setVal('search_tags', d['search_tags']);

        // Attempt to set sector (FK select) by matching text
        if ('sector' in d) {
            setVal('sector', d['sector']);
        }
        // Title may be updated
        if ('title' in d) setVal('title', d['title']);
    }

    document.addEventListener('DOMContentLoaded', function(){
        createButton();
        // admin inlines or dynamic forms may load later - observe
        const observer = new MutationObserver(()=> createButton());
        observer.observe(document.body, {childList:true, subtree:true});
    });
})();
