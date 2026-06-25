/**
 * demo-data.js
 * Mock data dictionary to back the Simulated Guided Tour.
 */

const DEMO_DATA = {
    // The demo meeting transcript prompt
    prompt: `Analizza questa trascrizione meeting e restituisci:
- summary breve
- decisioni prese
- action item
- rischi o punti aperti

Trascrizione:
Abbiamo deciso di rilasciare la nuova versione venerdì. Marco prepara il rollback plan, Giulia verifica i test finali e Daniele aggiorna la documentazione. Il rischio principale è che il modello locale sia troppo lento su macchine meno potenti.`,

    // Mock thinking process text showing reasoning path
    thinking: `<thought>
1. **Analisi della richiesta**: L'utente fornisce una trascrizione e richiede quattro elementi: un summary breve, le decisioni prese, gli action item e i rischi/punti aperti.
2. **Analisi del testo della trascrizione**:
   - "Abbiamo deciso di rilasciare la nuova versione venerdì." -> Decisione: rilascio venerdì.
   - "Marco prepara il rollback plan" -> Action item per Marco.
   - "Giulia verifica i test finali" -> Action item per Giulia.
   - "Daniele aggiorna la documentazione" -> Action item per Daniele.
   - "Il rischio principale è che il modello locale sia troppo lento su macchine meno potenti." -> Rischio: performance su hardware meno performante.
3. **Formattazione output**: L'utente ha richiesto un formato strutturato. Presento un output JSON pulito che rifletta esattamente le sezioni richieste in modo chiaro e deterministico.
4. **Validazione finale**: I dati mappano perfettamente le frasi della trascrizione.
</thought>
Sto estraendo le informazioni strutturate in formato JSON...`,

    // Mock final answer as a beautiful markdown JSON block
    response: `\`\`\`json
{
  "summary": "Il team ha pianificato il rilascio della nuova versione per venerdì, assegnando attività operative e identificando un rischio tecnico legato alle performance locali.",
  "decisions": [
    "Rilascio previsto venerdì"
  ],
  "action_items": [
    "Marco prepara il rollback plan",
    "Giulia verifica i test finali",
    "Daniele aggiorna la documentazione"
  ],
  "risks": [
    "Possibili performance insufficienti del modello locale su macchine meno potenti"
  ]
}
\`\`\``,

    // Statistics of generation
    stats: {
        tokens_per_second: 25.5,
        time_total_seconds: 7.21,
        output_tokens: 184,
        total_tokens: 295
    },

    // Simulated Server Logs streamed during the demo
    serverLogs: [
        "[14:30:01] INFO [local_llm_server.server]: Active model check initiated.",
        "[14:30:05] INFO [local_llm_server.server]: Incoming request: POST /v1/chat/completions",
        "[14:30:05] INFO [local_llm_server.engine]: Initializing context evaluation for current sequence...",
        "[14:30:06] INFO [local_llm_server.engine]: LlamaCppEngine - Prompt tokens: 111, System tokens: 24",
        "[14:30:07] INFO [local_llm_server.engine]: Processing prompt evaluation (batch size: 512)...",
        "[14:30:07] INFO [local_llm_server.engine]: Prompt evaluated in 1.12 seconds (120.5 tokens/sec)",
        "[14:30:08] INFO [local_llm_server.engine]: Generation started. Sampling temperature: 0.70",
        "[14:30:09] INFO [local_llm_server.engine]: [Token: 25] State evaluation: reasoning node <think> active",
        "[14:30:10] INFO [local_llm_server.engine]: [Token: 80] State evaluation: reasoning node <think> finished",
        "[14:30:11] INFO [local_llm_server.engine]: [Token: 120] Structuring constraints: JSON schema verification active",
        "[14:30:12] INFO [local_llm_server.engine]: Completed generating 184 tokens in 7.21 seconds (25.5 tokens/sec)",
        "[14:30:12] INFO [local_llm_server.server]: Response successfully sent back to ClosedRoom client (status: 200 OK)"
    ]
};
