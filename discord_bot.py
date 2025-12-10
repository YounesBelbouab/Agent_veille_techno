import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from veille_scraping import call_api_articles
from conversation_agent import ConversationAgent 

class DiscordBot(discord.Client):
    def __init__(self, conversation_agent):
        # Activation des intents
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        
        self.conversation_agent = conversation_agent
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        
        # --- Commande /ask existante ---
        @self.tree.command(name="ask", description="Pose une question à Jarvis")
        @app_commands.describe(question="Il est un peu enervé, fais attention à ce que tu racontes...")
        async def ask(interaction: discord.Interaction, question: str):
            await interaction.response.defer()
            try:
                response = self.conversation_agent.ask_llm(user_interaction=question)
                full_response = f"**Question :** {question}\n\n{response}"
                
                if len(full_response) > 2000:
                    full_response = full_response[:1990] + "..."
                
                await interaction.followup.send(full_response)
            except Exception as e:
                await interaction.followup.send(f"Une erreur est survenue : {e}")

        @self.tree.command(name="ask_veille", description="Lance une veille d'information")
        @app_commands.describe(
            sujet_veille="Le sujet ou les mots-clés de la veille",
            langue="Langue des articles (Sélectionner dans la liste)",
            jour="Nombre de jours à remonter",
            nombre_article="Nombre d'articles à récupérer"
        )
        @app_commands.choices(langue=[
            app_commands.Choice(name="Français", value="FR"),
            app_commands.Choice(name="English", value="EN")
        ])
        async def ask_veille(
            interaction: discord.Interaction, 
            sujet_veille: str, 
            langue: app_commands.Choice[str], 
            jour: int, 
            nombre_article: int
        ):
            
            if jour < 1 or nombre_article < 1:
                await interaction.response.send_message(
                    "❌ Erreur : Le nombre de jours et le nombre d'articles doivent être supérieurs à 0.", 
                    ephemeral=True
                )
                return

            await interaction.response.defer()
            
            try:
                response = call_api_articles(sujet=sujet_veille, langue=langue.value, jour=jour, nb_articles=nombre_article)
                
                # answer formatting for user
                header = (
                    f" ## Veille lancée \n" 
                    f"Sujet : {sujet_veille}\n"
                    f"Langue : {langue.name}\n"
                    f"Jours : {jour} | 📑 Articles : {nombre_article}\n"
                    f"-----------------------------------\n"
                )
                full_response = header + str(response)
                
                # limit message length
                if len(full_response) > 2000:
                    full_response = full_response[:1990] + "..."
                
                await interaction.followup.send(full_response)
                
            except Exception as e:
                await interaction.followup.send(f"Une erreur est survenue lors de la veille : {e}")

        await self.tree.sync()
        print("Commandes synchronisées (ask, ask_veille).")

    async def on_ready(self):
        print(f'Connecté en tant que {self.user} !')

if __name__ == "__main__":
    load_dotenv()
    discord_token = os.getenv('DISCORD_TOKEN')
    
    if not discord_token:
        print("Erreur : Token manquant dans le .env")
    else:
        agent = ConversationAgent()
        bot = DiscordBot(conversation_agent=agent)
        bot.run(discord_token)