package projet.emi.ai.chatbotuniversitaire.entity;

import jakarta.persistence.*;
import java.util.Set;

@Entity
@Table(name = "keywords")
public class Keyword {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String word;

    @ManyToMany(mappedBy = "keywords")
    private Set<Faq> faqs;

    // Générez les Getters et Setters (Alt+Insert dans IntelliJ)
}