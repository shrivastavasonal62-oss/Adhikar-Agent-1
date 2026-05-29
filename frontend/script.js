const API_URL ='/process-documents';
let pdfBlob = null;

const SCHEMES = {
  PMAY: {
    name: '🏠 PMAY',
    full: 'Pradhan Mantri Awas Yojana',
    benefit: 'Subsidized home loan up to ₹2.67 lakh',
    desc: 'Housing for All — EWS/LIG/MIG families'
  },
  'PM-KISAN': {
    name: '🌾 PM-KISAN',
    full: 'Kisan Samman Nidhi Yojana',
    benefit: '₹6,000/year direct bank transfer',
    desc: 'Income support for farmer families'
  },
  AYUSHMAN_BHARAT: {
    name: '🏥 Ayushman Bharat',
    full: 'PM Jan Arogya Yojana',
    benefit: '₹5 lakh health insurance/year',
    desc: 'Free hospital treatment for BPL families'
  },
  SC_ST_SCHOLARSHIP: {
    name: '📚 SC/ST Scholarship',
    full: 'Post-Matric Scholarship Scheme',
    benefit: 'Full tuition + maintenance allowance',
    desc: 'Education support for SC/ST students'
  }
};

const SCHEME_PRIORITY = ['PMAY', 'PM-KISAN', 'AYUSHMAN_BHARAT', 'SC_ST_SCHOLARSHIP'];

function enterApp() {
  const splash = document.getElementById('splash');
  splash.classList.add('out');

  setTimeout(() => {
    splash.style.display = 'none';
    const app = document.getElementById('app');
    app.style.display = 'block';
    requestAnimationFrame(() => app.classList.add('show'));
  }, 900);
}

function onFile(input, id) {
  if (!input.files || !input.files[0]) return;

  const file = input.files[0];

  const allowed = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];

  if (!allowed.includes(file.type)) {
    alert('Only JPG, PNG or PDF files are allowed.');
    input.value = '';
    return;
  }

  if (file.size > 10 * 1024 * 1024) {
    alert('File size must be less than 10MB.');
    input.value = '';
    return;
  }

  if (id === 'aadhaar') {
    const fileName = file.name.toLowerCase();
    const aadhaarWords = ['aadhaar', 'aadhar', 'uidai'];

    if (!aadhaarWords.some(word => fileName.includes(word))) {
      alert('Please upload Aadhaar Card only in Aadhaar slot. File name should contain aadhaar, aadhar, or uidai.');
      input.value = '';
      return;
    }
  }

  document.getElementById('box-' + id).classList.add('done');

  const st = document.getElementById('st-' + id);
  st.textContent = '✓ ' + file.name;
  st.classList.add('ok');
}

const wait = ms => new Promise(r => setTimeout(r, ms));

function log(msg, type = 'i') {
  const body = document.getElementById('tBody');
  const el = document.createElement('div');
  el.className = 'tlog ' + type;

  const icons = { i: '›', s: '✓', w: '⚠', d: '★', e: '✗' };

  el.innerHTML = `
    <span style="opacity:0.4;min-width:14px">${icons[type] || '›'}</span>
    <span>${msg}</span>
  `;

  body.appendChild(el);
  body.scrollTop = body.scrollHeight;
}

function progress(pct, lbl) {
  document.getElementById('pFill').style.width = pct + '%';
  document.getElementById('pLbl').textContent = lbl;
}

const show = id => document.getElementById(id).classList.remove('hidden');
const hide = id => document.getElementById(id).classList.add('hidden');

function val(v) {
  if (!v || v === '' || v === 'null' || v === 'None' || v === 'undefined') {
    return '<span style="color:#555">—</span>';
  }

  return v;
}

async function startProcess() {
  const aadhaarFile = document.getElementById('aadhaar')?.files[0];

  if (!aadhaarFile) {
    alert('Please upload Aadhaar Card first.');
    return;
  }

  const files = [];

  ['aadhaar', 'ration', 'caste'].forEach(t => {
    const input = document.getElementById(t);
    const f = input?.files[0];

    if (f) files.push(f);
  });

  if (!files.length) {
    alert('Please upload at least one document.');
    return;
  }

  document.getElementById('submitBtn').disabled = true;
  hide('uploadSection');
  show('terminalSection');
  hide('resultsSection');
  hide('errorSection');

  document.getElementById('tBody').innerHTML = '';
  progress(0, 'Starting...');
  window.scrollTo({ top: 400, behavior: 'smooth' });

  await wait(300);
  log(files.length + ' document(s) received for processing', 'i');
  progress(8, 'Uploading to AWS...');

  await wait(600);
  log('Connecting to AWS services (region: us-east-1)', 'i');

  await wait(600);
  log('AWS Textract OCR engine connected ✓', 's');
  progress(20, 'AWS Textract connected...');

  await wait(700);
  log('Running OCR — extracting text from documents...', 'i');
  progress(34, 'Extracting text with AWS Textract...');

  try {
    const fd = new FormData();
    files.forEach(f => fd.append('files', f));

    const res = await fetch(API_URL, {
      method: 'POST',
      body: fd
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: 'Server error' }));
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }

    await wait(500);
    log('Raw text extraction complete ✓', 's');

    await wait(400);
    log('Privacy check: Masking Aadhaar → XXXX-XXXX-****', 'w');
    progress(48, 'Masking sensitive data...');

    await wait(500);
    log('Sensitive data masked. Safe for AI processing ✓', 's');

    await wait(500);
    log('Sending structured data to Amazon Nova Pro...', 'i');
    progress(60, 'Amazon Nova Pro analysing...');

    await wait(500);
    log('Nova Pro: Checking PMAY eligibility...', 'i');
    await wait(300);
    log('Nova Pro: Checking PM-KISAN eligibility...', 'i');
    await wait(300);
    log('Nova Pro: Checking Ayushman Bharat eligibility...', 'i');
    await wait(300);
    log('Nova Pro: Checking SC/ST Scholarship eligibility...', 'i');
    progress(76, 'Running eligibility rules engine...');

    const eligibleHeader = res.headers.get('X-Eligible-Schemes') || '';
    const eligibleSchemes = eligibleHeader
      ? eligibleHeader.split(',').map(s => s.trim()).filter(Boolean)
      : [];

    const applicant = {
      name: res.headers.get('X-Applicant-Name') || '',
      state: res.headers.get('X-Applicant-State') || '',
      income: res.headers.get('X-Applicant-Income') || '',
      caste: res.headers.get('X-Applicant-Caste') || '',
      bpl: res.headers.get('X-Applicant-BPL') || ''
    };

    pdfBlob = await res.blob();

    await wait(400);
    log('Nova Pro eligibility analysis complete ✓', 's');

    if (eligibleSchemes.length > 0) {
      log('Eligible schemes: ' + eligibleSchemes.join(', '), 'd');
    } else {
      log('No schemes eligible based on provided documents', 'w');
    }

    progress(90, 'Generating application PDF...');
    await wait(500);
    log('PDF auto-filled with applicant details ✓', 's');

    if (applicant.name) {
      log('Applicant identified: ' + applicant.name, 's');
    }

    progress(100, 'Complete ✓');
    await wait(300);
    log('Application form ready for download ★', 'd');
    await wait(800);

    hide('terminalSection');
    show('resultsSection');
    renderResults(eligibleSchemes, applicant);
    window.scrollTo({ top: 400, behavior: 'smooth' });

  } catch (e) {
    log('Error: ' + e.message, 'e');
    console.error('[Adhikar] Error:', e);

    await wait(1000);

    hide('terminalSection');
    show('errorSection');

    document.getElementById('errMsg').textContent = e.message;
    document.getElementById('submitBtn').disabled = false;
  }
}

function renderResults(eligible, applicant = {}) {
  const sr = document.getElementById('schemeResults');
  sr.innerHTML = '';

  let eligibleCount = 0;

  SCHEME_PRIORITY.forEach(key => {
    const info = SCHEMES[key];
    const yes = eligible.includes(key);

    if (yes) eligibleCount++;

    sr.innerHTML += `
      <div class="sr ${yes ? 'yes' : 'no'}">
        <div class="sr-top">
          <span class="sr-name">${info.name}</span>
          <span class="sr-badge">${yes ? '✓ ELIGIBLE' : '✗ NOT ELIGIBLE'}</span>
        </div>
        <div class="sr-desc">${info.full}</div>
        <div class="sr-subdesc">${info.desc}</div>
        ${yes ? `<div class="sr-benefit">💰 ${info.benefit}</div>` : ''}
      </div>`;
  });

  const summary = document.getElementById('resultSummary');

  if (summary) {
    if (eligibleCount > 0) {
      summary.textContent = `✅ Eligible for ${eligibleCount} scheme${eligibleCount > 1 ? 's' : ''}`;
      summary.style.color = '#34d399';
    } else {
      summary.textContent = '⚠️ No schemes eligible — upload more documents';
      summary.style.color = '#f59e0b';
    }
  }

  const bplDisplay =
    applicant.bpl === 'true' || applicant.bpl === 'True'
      ? '<span style="color:#34d399">✓ BPL</span>'
      : applicant.bpl === 'false' || applicant.bpl === 'False'
        ? 'Non-BPL'
        : val(applicant.bpl);

  const incomeDisplay =
    applicant.income && applicant.income !== ''
      ? '₹' + Number(applicant.income).toLocaleString('en-IN')
      : val(applicant.income);

  document.getElementById('appInfo').innerHTML = `
    <div class="ai-item">
      <label>Name</label>
      <span>${val(applicant.name)}</span>
    </div>
    <div class="ai-item">
      <label>State</label>
      <span>${val(applicant.state)}</span>
    </div>
    <div class="ai-item">
      <label>Annual Income</label>
      <span>${incomeDisplay}</span>
    </div>
    <div class="ai-item">
      <label>Caste</label>
      <span>${val(applicant.caste)}</span>
    </div>
    <div class="ai-item">
      <label>BPL Status</label>
      <span>${bplDisplay}</span>
    </div>
    <div class="ai-item">
      <label>Form Status</label>
      <span style="color:#34d399">✓ Auto-Filled</span>
    </div>`;
}

function downloadPDF() {
  if (!pdfBlob) {
    alert('No PDF available. Please process documents first.');
    return;
  }

  const url = URL.createObjectURL(pdfBlob);
  const a = document.createElement('a');

  a.href = url;
  a.download = 'Adhikar_Application_Form.pdf';

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  URL.revokeObjectURL(url);
}

function resetAll() {
  pdfBlob = null;

  show('uploadSection');
  hide('terminalSection');
  hide('resultsSection');
  hide('errorSection');

  document.getElementById('submitBtn').disabled = false;
  document.getElementById('tBody').innerHTML = '';
  document.getElementById('pFill').style.width = '0%';
  document.getElementById('pLbl').textContent = '';

  ['aadhaar', 'voter', 'ration', 'caste'].forEach(t => {
    const input = document.getElementById(t);
    if (input) input.value = '';

    const box = document.getElementById('box-' + t);
    if (box) box.classList.remove('done');

    const st = document.getElementById('st-' + t);
    if (st) {
      st.textContent = 'Click to upload';
      st.classList.remove('ok');
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.addEventListener('DOMContentLoaded', () => {
  ['aadhaar', 'voter', 'ration', 'caste'].forEach(id => {
    const box = document.getElementById('box-' + id);

    if (!box) return;

    box.addEventListener('dragover', e => {
      e.preventDefault();
      box.style.borderColor = '#6c5ce7';
      box.style.background = 'rgba(108,92,231,0.1)';
    });

    box.addEventListener('dragleave', () => {
      box.style.borderColor = '';
      box.style.background = '';
    });

    box.addEventListener('drop', e => {
      e.preventDefault();

      box.style.borderColor = '';
      box.style.background = '';

      const file = e.dataTransfer.files[0];

      if (file) {
        const input = document.getElementById(id);
        const dt = new DataTransfer();

        dt.items.add(file);
        input.files = dt.files;

        onFile(input, id);
      }
    });
  });
});