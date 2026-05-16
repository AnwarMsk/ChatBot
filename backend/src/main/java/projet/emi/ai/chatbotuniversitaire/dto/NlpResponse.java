package projet.emi.ai.chatbotuniversitaire.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

/**
 * Maps the JSON response returned by the Flask NLP microservice.
 *
 * Flask returns:
 * {
 *   "reponse":          "La bibliothèque est ouverte...",
 *   "score":            0.8412,
 *   "question_matchee": "Quels sont les horaires de la bibliothèque ?",
 *   "trouve":           true
 * }
 */
@Data
public class NlpResponse {

    /** The answer text to return to the user. */
    private String reponse;

    /** Cosine similarity score (0 to 1). Higher = more confident. */
    private double score;

    /** The FAQ question that was matched by the NLP engine. */
    @JsonProperty("question_matchee")
    private String questionMatchee;

    /** True if a match above the threshold was found, false otherwise. */
    private boolean trouve;
}
