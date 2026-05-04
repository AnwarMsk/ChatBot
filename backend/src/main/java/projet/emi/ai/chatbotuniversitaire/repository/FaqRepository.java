package projet.emi.ai.chatbotuniversitaire.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import projet.emi.ai.chatbotuniversitaire.entity.Faq;

import java.util.List;

@Repository
public interface FaqRepository extends JpaRepository<Faq, Long> {

    @Query("SELECT f FROM Faq f JOIN f.keywords k WHERE LOWER(k.word) = LOWER(:word)")
    List<Faq> findByKeyword(@Param("word") String word);
}