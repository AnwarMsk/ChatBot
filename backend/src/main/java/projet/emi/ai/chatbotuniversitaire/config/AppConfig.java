package projet.emi.ai.chatbotuniversitaire.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Configuration
public class AppConfig {

    @Value("${nlp.service.timeout-ms:5000}")
    private int timeoutMs;

    /**
     * RestTemplate configured with connect + read timeouts.
     * Used by NlpService to call the Flask microservice.
     * Timeout prevents the chatbot from hanging if Flask is slow or down.
     */
    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofMillis(timeoutMs));
        factory.setReadTimeout(Duration.ofMillis(timeoutMs));
        return new RestTemplate(factory);
    }
}
