from datetime import datetime

def determine_theme(title, content):
    """
    Détermine le thème principal de l'article
    """
    themes_keywords = {
        'Data Engineering': ['data', 'etl', 'sql', 'python', 'pandas', 'pipeline', 'transformation'],
        'Cloud & DevOps': ['aws', 'cloud', 'lambda', 'serverless', 'kubernetes', 'docker'],
        'AI & Machine Learning': ['ai', 'machine learning', 'llm', 'model', 'neural', 'copilot'],
        'Security': ['security', 'authentication', 'vulnerability', 'threat', 'encryption'],
        'Development': ['development', 'code', 'programming', 'api', 'framework']
    }
    
    text = (title + " " + content).lower()
    
    theme_scores = {}
    for theme, keywords in themes_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text)
        theme_scores[theme] = score
    
    return max(theme_scores, key=theme_scores.get) if max(theme_scores.values()) > 0 else 'Tech'

def generate_newsletter_html(articles):
    """
    Génère le HTML de la newsletter avec les articles fournis
    """
    
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Newsletter</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">
                                Tech Weekly Digest
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #e0e7ff; font-size: 14px;">
                                """ + datetime.now().strftime("%d %B %Y") + """
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Introduction -->
                    <tr>
                        <td style="padding: 30px 30px 20px 30px;">
                            <p style="margin: 0; color: #4b5563; font-size: 15px; line-height: 1.6;">
                                Découvrez les dernières actualités tech soigneusement sélectionnées pour vous.
                            </p>
                        </td>
                    </tr>
"""
    
    for article in articles:
        word_count = len(article['content'].split())
        reading_time = max(1, round(word_count / 200))
        preview = article['content'][:200].strip() + "..."
        theme = determine_theme(article['title'], article['content'])
        
        html += f"""
                    <!-- Article Card -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <table role="presentation" style="width: 100%; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 24px;">
                                        <!-- Theme Badge -->
                                        <div style="margin-bottom: 12px;">
                                            <span style="display: inline-block; background-color: #eff6ff; color: #1e40af; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
                                                {theme}
                                            </span>
                                        </div>
                                        
                                        <!-- Title -->
                                        <h2 style="margin: 0 0 12px 0; color: #111827; font-size: 20px; font-weight: 600; line-height: 1.3;">
                                            <a href="{article['url']}" style="color: #111827; text-decoration: none;">
                                                {article['title']}
                                            </a>
                                        </h2>
                                        
                                        <!-- Meta Info -->
                                        <div style="margin-bottom: 16px; color: #6b7280; font-size: 13px;">
                                            <span style="margin-right: 12px;">📅 {article['date']}</span>
                                            <span style="margin-right: 12px;">⏱️ {reading_time} min de lecture</span>
                                            <span>📰 {article['source']}</span>
                                        </div>
                                        
                                        <!-- Preview -->
                                        <p style="margin: 0 0 16px 0; color: #4b5563; font-size: 14px; line-height: 1.6;">
                                            {preview}
                                        </p>
                                        
                                        <!-- CTA Button -->
                                        <a href="{article['url']}" style="display: inline-block; background-color: #667eea; color: #ffffff; padding: 10px 24px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 500;">
                                            Lire l'article →
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
"""
    
    html += """
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px; background-color: #f9fafb; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 13px;">
                                Vous recevez cet email car vous êtes abonné à notre newsletter tech.
                            </p>
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                © 2025 Tech Weekly Digest. Tous droits réservés.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    return html
