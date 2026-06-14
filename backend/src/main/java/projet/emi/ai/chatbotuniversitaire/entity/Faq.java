package projet.emi.ai.chatbotuniversitaire.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.util.Set;

@Entity
@Table(name = "faqs")
public class Faq {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String question;
    @Setter
    @Getter
    @Column(columnDefinition = "TEXT")
    private String answer;

    @ManyToMany
    @JoinTable(
            name = "faq_keywords",
            joinColumns = @JoinColumn(name = "faq_id"),
            inverseJoinColumns = @JoinColumn(name = "keyword_id")
    )
    private Set<Keyword> keywords;

}
