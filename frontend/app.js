const questionForm = document.querySelector('#question-form');
const questionInput = document.querySelector('#question-input');
const conversation = document.querySelector('#conversation');
const sendButton = questionForm.querySelector('button[type="submit"]');
let answerSequence = 0;

function addMessage(text, role) {
  const message = document.createElement('div');
  message.className = `message ${role}-message`;

  if (role === 'assistant') {
    const label = document.createElement('span');
    label.className = 'message-label';
    label.textContent = 'SAMVIDHAN';
    message.append(label);
  }

  const paragraph = document.createElement('p');
  paragraph.textContent = text;
  message.append(paragraph);
  conversation.append(message);
  conversation.scrollTop = conversation.scrollHeight;
  return message;
}

function addAnswer(text, sources) {
  const message = document.createElement('div');
  message.className = 'message assistant-message';

  const label = document.createElement('span');
  label.className = 'message-label';
  label.textContent = 'SAMVIDHAN';

  const sourceNumberMap = new Map();
  const sourceDetailsMap = new Map();
  const validSources = sources.filter(
    (source) => source && Number.isInteger(Number(source.id)),
  );
  const answerId = ++answerSequence;

  for (const source of validSources) {
    const sourceId = Number(source.id);
    const details = document.createElement('details');
    details.className = 'source-item';
    details.id = `answer-${answerId}-source-${sourceId}`;

    const summary = document.createElement('summary');
    summary.textContent = `Source ${sourceId} · ${source.label || 'Retrieved passage'}`;

    const excerpt = document.createElement('p');
    excerpt.className = 'source-text';
    excerpt.textContent = typeof source.text === 'string' ? source.text : '';

    details.append(summary, excerpt);
    sourceNumberMap.set(sourceId, source);
    sourceDetailsMap.set(sourceId, details);
  }

  const paragraph = document.createElement('p');
  const citationPattern = /\[Source\s+(\d+)\]/g;
  let lastIndex = 0;
  let match;

  while ((match = citationPattern.exec(text)) !== null) {
    paragraph.append(document.createTextNode(text.slice(lastIndex, match.index)));
    const sourceId = Number(match[1]);

    if (sourceNumberMap.has(sourceId)) {
      const citation = document.createElement('button');
      citation.type = 'button';
      citation.className = 'citation-link';
      citation.textContent = match[0];
      citation.setAttribute('aria-label', `Show retrieved passage for source ${sourceId}`);
      citation.addEventListener('click', () => {
        const details = sourceDetailsMap.get(sourceId);
        details.open = true;
        details.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
      paragraph.append(citation);
    } else {
      const unmatched = document.createElement('span');
      unmatched.className = 'citation-unmatched';
      unmatched.textContent = `[Source ${sourceId} — unavailable]`;
      paragraph.append(unmatched);
    }

    lastIndex = citationPattern.lastIndex;
  }
  paragraph.append(document.createTextNode(text.slice(lastIndex)));
  message.append(label, paragraph);

  if (validSources.length) {
    const sourceList = document.createElement('section');
    sourceList.className = 'source-list';
    sourceList.setAttribute('aria-label', 'Retrieved passages');

    const heading = document.createElement('span');
    heading.className = 'source-list-heading';
    heading.textContent = 'RETRIEVED PASSAGES';
    sourceList.append(heading, ...sourceDetailsMap.values());
    message.append(sourceList);
  }

  conversation.append(message);
  conversation.scrollTop = conversation.scrollHeight;
  return message;
}

function addTypingIndicator() {
  const message = document.createElement('div');
  message.className = 'message assistant-message';
  message.setAttribute('aria-label', 'Samvidhan is preparing an answer');

  const label = document.createElement('span');
  label.className = 'message-label';
  label.textContent = 'SAMVIDHAN';

  const dots = document.createElement('span');
  dots.className = 'typing-dots';
  dots.setAttribute('aria-hidden', 'true');
  dots.innerHTML = '<span></span><span></span><span></span>';
  message.append(label, dots);
  conversation.append(message);
  conversation.scrollTop = conversation.scrollHeight;
  return message;
}

async function ask(question) {
  addMessage(question, 'user');
  const typingIndicator = addTypingIndicator();
  sendButton.disabled = true;

  try {
    const response = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }

    const data = await response.json();
    if (typeof data.answer !== 'string' || !data.answer.trim()) {
      throw new Error('The assistant returned an empty answer.');
    }
    typingIndicator.remove();
    addAnswer(data.answer, Array.isArray(data.sources) ? data.sources : []);
  } catch (error) {
    typingIndicator.remove();
    addMessage(
      'I could not get an answer just now. Please check that the Constitution assistant is running, then try again.',
      'assistant',
    );
  } finally {
    sendButton.disabled = false;
    questionInput.focus();
  }
}

questionForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question || sendButton.disabled) return;
  questionInput.value = '';
  questionInput.style.height = 'auto';
  ask(question);
});

questionInput.addEventListener('input', () => {
  questionInput.style.height = 'auto';
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 130)}px`;
});

questionInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    questionForm.requestSubmit();
  }
});

document.querySelectorAll('.suggestion').forEach((button) => {
  button.addEventListener('click', () => {
    questionInput.value = button.dataset.prompt;
    questionForm.requestSubmit();
  });
});
