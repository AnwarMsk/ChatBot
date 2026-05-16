package projet.emi.ai.chatbotuniversitaire.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import projet.emi.ai.chatbotuniversitaire.dto.NlpResponse;

import java.util.Map;
import java.util.Optional;

/**
 * Service responsible for communicating with the Python Flask NLP microservice.
 *
 * It sends the user's question to Flask and returns the semantic answer.
 * If Flask is unavailable (down, timeout, network error), it returns empty
 * so the caller can fall back to V1 keyword search.
 */
@Slf4j
@Service
public class NlpService {

    private final RestTemplate restTemplate;

    @Value("${nlp.service.url}")
    private String nlpServiceUrl;

    public NlpService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * Sends the question to the Flask NLP microservice.
     *
     * @param question the raw user question
     * @return Optional containing the answer if NLP found a match,
     *         or empty if Flask is unavailable or no match was found
     */
    public Optional<String> askNlp(String question) {
        try {
            Map<String, String> payload = Map.of("question", question);

            NlpResponse response = restTemplate.postForObject(
                    nlpServiceUrl + "/ask",
                    payload,
                    NlpResponse.class
            );

            if (response != null && response.isTrouve()) {
                log.debug("NLP match found — score: {}, question: '{}'",
                        response.getScore(), response.getQuestionMatchee());
                return Optional.of(response.getReponse());
            }

            // NLP engine returned a response but found no good match
            log.debug("NLP returned no match (score too low).");
            return Optional.empty();

        } catch (RestClientException e) {
            // Flask is down, timed out, or unreachable
            log.warn("NLP service unreachable at {} — falling back to V1. Reason: {}",
                    nlpServiceUrl, e.getMessage());
            return Optional.empty();
        }
    }

    /**
     * Checks if the Flask NLP microservice is up and ready.
     *
     * @return true if the /health endpoint responds successfully
     */
    public boolean isAvailable() {
        try {
            restTemplate.getForObject(nlpServiceUrl + "/health", Map.class);
            return true;
        } catch (RestClientException e) {
            log.warn("NLP health check failed: {}", e.getMessage());
            return false;
        }
    }
}
