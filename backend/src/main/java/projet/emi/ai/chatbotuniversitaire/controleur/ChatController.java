package projet.emi.ai.chatbotuniversitaire.controleur;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import projet.emi.ai.chatbotuniversitaire.entity.Faq;
import projet.emi.ai.chatbotuniversitaire.repository.FaqRepository;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/chatbot")
@CrossOrigin(origins = "http://localhost:4200")
public class ChatController {

    @Autowired
    private FaqRepository faqRepository;

    @PostMapping("/ask")
    public Map<String, String> handleQuestion(@RequestBody Map<String, String> payload) {


        String question = payload.get("question");


        String cleanedQuestion = question.toLowerCase().replaceAll("[^a-zA-Z0-9 ]", "");
        String[] words = cleanedQuestion.split("\\s+");

        String botResponse = "Désolé, je n'ai pas trouvé d'information sur ce sujet.";


        for (String word : words) {
            List<Faq> results = faqRepository.findByKeyword(word);
            if (!results.isEmpty()) {
                botResponse = results.get(0).getAnswer();
                break;
            }
        }


        Map<String, String> response = new HashMap<>();
        response.put("answer", botResponse);

        return response;
    }
}