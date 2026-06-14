package projet.emi.ai.chatbotuniversitaire.exception;

/**
 * Exception thrown when the Flask NLP microservice is down, times out, or is unreachable.
 */
public class NlpServiceUnavailableException extends RuntimeException {
    public NlpServiceUnavailableException(String message, Throwable cause) {
        super(message, cause);
    }
}
