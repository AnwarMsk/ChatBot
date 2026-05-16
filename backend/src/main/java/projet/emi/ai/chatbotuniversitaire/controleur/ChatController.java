package projet.emi.ai.chatbotuniversitaire.controleur;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import projet.emi.ai.chatbotuniversitaire.entity.Faq;
import projet.emi.ai.chatbotuniversitaire.repository.FaqRepository;
import projet.emi.ai.chatbotuniversitaire.service.NlpService;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Slf4j
@RestController
@RequestMapping("/api/chatbot")
@CrossOrigin(origins = "http://localhost:4200")
public class ChatController {

    private final NlpService nlpService;
    private final FaqRepository faqRepository;

    public ChatController(NlpService nlpService, FaqRepository faqRepository) {
        this.nlpService = nlpService;
        this.faqRepository = faqRepository;
    }

    @PostMapping("/ask")
    public Map<String, Object> handleQuestion(@RequestBody Map<String, String> payload) {

        String question = payload.get("question");
        if (question == null || question.isBlank()) {
            return Map.of("answer", "Veuillez poser une question.", "degraded", false);
        }

        // ── V2 : NLP semantic search (Flask microservice) ──────────────
        Optional<String> nlpAnswer = nlpService.askNlp(question);
        if (nlpAnswer.isPresent()) {
            return buildResponse(nlpAnswer.get(), false);
        }

        // ── V1 fallback : keyword search in PostgreSQL ──────────────────
        log.warn("Falling back to V1 keyword search for question: '{}'", question);

        String cleanedQuestion = question.toLowerCase().replaceAll("[^a-zA-Z0-9 ]", "");
        String[] words = cleanedQuestion.split("\\s+");

        for (String word : words) {
            List<Faq> results = faqRepository.findByKeyword(word);
            if (!results.isEmpty()) {
                // Found a V1 match — return it with degraded=true so the UI can warn the user
                return buildResponse(results.get(0).getAnswer(), true);
            }
        }

        // Nothing found in either V1 or V2
        return buildResponse("Désolé, je n'ai pas trouvé d'information sur ce sujet. Veuillez contacter la scolarité de l'EMI.", false);
    }

    private Map<String, Object> buildResponse(String answer, boolean degraded) {
        Map<String, Object> response = new HashMap<>();
        response.put("answer", answer);
        response.put("degraded", degraded);  // true = V1 fallback was used
        return response;
    }
}