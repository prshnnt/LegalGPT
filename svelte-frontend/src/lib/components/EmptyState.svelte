<script lang="ts">
  import { Scale, Globe, FileText, BookOpen } from '@lucide/svelte';
  import type { Attachment } from '../types/chat';

  export let onExampleClick: (text: string, attachments: Attachment[]) => void;

  const examples = [
    {
      icon: BookOpen,
      text: 'Explain Article 21',
      prompt: 'Can you explain Article 21 of the Constitution of India in detail, including its significance and landmark judgments?',
    },
    {
      icon: Scale,
      text: 'BNS vs IPC differences',
      prompt: 'What are the key differences between Bharatiya Nyaya Sanhita (BNS) and the Indian Penal Code (IPC)?',
    },
    {
      icon: Globe,
      text: 'Recent SC judgments',
      prompt: 'What are some recent important Supreme Court judgments? Please search the web for the latest information.',
    },
    {
      icon: FileText,
      text: 'Analyze a legal document',
      prompt: "I have a legal document that I need help understanding. I'll upload it and need you to explain the key legal points.",
    },
  ];
</script>

<div class="empty-state">
  <div class="empty-hero">
    <div class="empty-logo">
      <Scale size={30} color="rgba(30,15,5,0.90)" strokeWidth={2.2} />
    </div>
    <h1 class="empty-title">LegalGPT</h1>
    <p class="empty-sub">
      Your AI assistant for studying Indian law —<br />
      Constitution, BNS, BNSS, case laws &amp; more
    </p>
  </div>

  <div class="examples-grid">
    {#each examples as ex}
      <button
        type="button"
        class="example-card"
        on:click={() => onExampleClick(ex.prompt, [])}
      >
        <div class="example-icon-wrap">
          <svelte:component this={ex.icon} size={16} />
        </div>
        <span class="example-text">{ex.text}</span>
      </button>
    {/each}
  </div>

  <div class="empty-disclaimer">
    <strong>Note:</strong> LegalGPT is an educational tool for law students.
    Always verify legal information with official sources and consult
    qualified legal professionals for advice.
  </div>
</div>
