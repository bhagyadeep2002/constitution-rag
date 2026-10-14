const questionForm = document.querySelector('#question-form');
const questionInput = document.querySelector('#question-input');
const conversation = document.querySelector('#conversation');
const sendButton = questionForm.querySelector('button[type="submit"]');

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
    addMessage(data.answer, 'assistant');
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
