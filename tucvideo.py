import os
import json
import random
import time
import openai
from openai import AzureOpenAI
import requests
import datetime
try:
    from requests_oauthlib import OAuth1Session
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    print("Warning: requests_oauthlib not installed. Twitter API v1.1 upload will be disabled.")
    # Mock class to prevent NameError on type hints or usage
    class OAuth1Session: pass

from PIL import Image
import base64
try:
    # MoviePy v0/v1
    try:
        from moviepy import VideoFileClip, ImageClip, CompositeVideoClip
    except ImportError:
        print("Error: moviepy not found. Please pip install moviepy")
        sys.exit(1)
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        # MoviePy v2
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from moviepy.video.VideoClip import ImageClip
        from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False
        print("Warning: moviepy not installed. Video processing will be disabled.")

import shutil  # Added to locate ffmpeg executable
import subprocess  # ensure subprocess is available before use

used_video_prompts = set()
used_text_prompts = set()

# Twitter API credentials
consumer_key = 'W3pTNOgIreoJXDVET5i3rUBZE'
consumer_secret = 'VwbeIkAXk0v13ODZ64EckO78jrAqtVK4C61XicPsxv2Wv9Wdy1'

oauth = None  # Will be assigned after setup

# OpenAI API key for text generation
client = AzureOpenAI(
    api_key="aefad978082243b2a79e279b203efc29",  
    api_version="2025-04-01-preview",
    azure_endpoint="https://Panopticon.openai.azure.com/"
)

# Azure OpenAI Video Generation API details
AZURE_VIDEO_API_KEY = "aefad978082243b2a79e279b203efc29"
AZURE_VIDEO_ENDPOINT = "https://panopticon.openai.azure.com/openai/v1/video/generations/jobs"
AZURE_VIDEO_API_VERSION = "preview"

# Pillow >=10 removed the ANTIALIAS constant; add a fallback for compatibility
if not hasattr(Image, "ANTIALIAS"):
    # Map the removed constant to the recommended replacement so legacy code keeps working
    Image.ANTIALIAS = Image.Resampling.LANCZOS  # type: ignore[attr-defined]

def setup_twitter_oauth():
    global oauth
    request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)
    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        print("There may have been an issue with the consumer_key or consumer_secret you entered.")
        raise

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    print("Got OAuth token: %s" % resource_owner_key)

    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print("Please go here and authorize: %s" % authorization_url)
    verifier = input("Paste the PIN here: ")

    access_token_url = "https://api.twitter.com/oauth/access_token"
    oauth2 = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    oauth_tokens = oauth2.fetch_access_token(access_token_url)

    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )
    return oauth

# Define the modular system prompts
framework_prompts = {
    "0th Order": """0th Order Thinking: Position 📍
    Kaizen (改善) — Observe: Identify current position and make small improvements.
    Type of Observable Phenomenon: Basic Existence
    Mathematical Object: Point — Represents a specific location in space.
    Graph Object: Point — A single node on a graph, indicating a precise position.
    Abrahamic Theology: Judaism, Christianity, Islam — Emphasizes the foundational relationship with God and understanding one's place in creation.
    Non-Abrahamic Theology: Hinduism (Vedic) — Emphasizes one's dharma (duty) and position in the cosmic order.
    Eastern Hermeneutics: Vedic Hermeneutics — Understanding one's role in the universe through sacred texts.
    Classical Western Hermeneutics: Aristotelian Philosophy — Focuses on categorizing and understanding the essence of being.
    Modern Western Hermeneutics: Phenomenology (Heidegger) — Focuses on the immediate experience and being in the world.
    Economics: Microeconomics — Observes the individual position within markets, focusing on supply and demand.
    Ecology: Ecosystem Observation — Identifies an organism's specific role within its habitat.
    Schizoanalysis: Desiring-Machines (Deleuze & Guattari) — Focuses on the individual as a point of desire within social and psychological networks.
    Work: Observe your current role and responsibilities. Identify small areas for improvement.
    Life: Focus on your present circumstances. Make minor adjustments to enhance your daily life.
    Social: Recognize existing social structures. Make incremental changes to improve community dynamics.""",

        "1st Order": """1st Order Thinking: Velocity 🌠
    Ikigai (生き甲斐) — Process: Align activities with your purpose, moving forward with intention.
    Type of Observable Phenomenon: Directional Change
    Mathematical Object: Line Segment — Represents a path from one point to another.
    Graph Object: Line — A straight path connecting two points, indicating direction and progress.
    Abrahamic Theology: Christianity — Emphasizes the journey of faith and alignment with God's will.
    Non-Abrahamic Theology: Taoism — Emphasizes the flow of life and aligning with the Tao (the way).
    Eastern Hermeneutics: Confucianism — Emphasizes continuous learning and self-cultivation.
    Classical Western Hermeneutics: Stoicism (Epictetus, Marcus Aurelius) — Focuses on aligning actions with nature and rationality.
    Modern Western Hermeneutics: Existentialism (Sartre) — Focuses on creating meaning and purpose through actions.
    Economics: Growth Economics — Focuses on the progression of economic development over time.
    Ecology: Population Dynamics — Examines the growth and movement of species within ecosystems.
    Schizoanalysis: Flows of Desire (Deleuze & Guattari) — Analyzes the flow of desires and its influence on personal and social dynamics.
    Work: Process your career trajectory. Align tasks with your greater professional purpose.
    Life: Identify activities that align with your passions and values. Pursue them with mindful progress.
    Social: Support social initiatives that resonate with your values. Help drive forward meaningful change.""",

        "2nd Order": """2nd Order Thinking: Acceleration 🚀
    Shoshin (初心) — Integrate: Embrace change with a beginner's mind, accelerating growth.
    Type of Observable Phenomenon: Rate of Change
    Mathematical Object: Curve — Represents the changing rate of progress over time.
    Graph Object: Curve — A smooth, continuous path showing the rate of change.
    Abrahamic Theology: Islam — Emphasizes continuous submission and growth in faith (Iman).
    Non-Abrahamic Theology: Buddhism — Emphasizes continuous self-improvement and the path to enlightenment.
    Eastern Hermeneutics: Taoism — Emphasizes the natural flow and adaptability of life.
    Classical Western Hermeneutics: Platonism — Focuses on the realm of forms and the importance of education in perceiving true reality.
    Modern Western Hermeneutics: Pragmatism (Dewey) — Focuses on adapting to change through practical experience and learning.
    Economics: Keynesian Economics — Focuses on understanding the dynamics of acceleration and deceleration in economic activities.
    Ecology: Succession Dynamics — Studies the changes in species composition in an ecosystem over time.
    Schizoanalysis: Assemblages (Deleuze & Guattari) — Examines how diverse elements come together to form new connections and systems of desire.
    Work: Integrate new knowledge and skills. Approach challenges with curiosity.
    Life: Embrace life changes with an open, learning mindset. Accelerate personal development.
    Social: Foster community growth by integrating fresh perspectives and innovative ideas.""",

        "3rd Order": """3rd Order Thinking: Jerk ⚡
    Kintsugi (金継ぎ) — Observe: Recognize and appreciate sudden changes and imperfections.
    Type of Observable Phenomenon: Sudden Change
    Mathematical Object: Knot — Represents abrupt changes or intersections.
    Graph Object: Saddle Point — A point on a surface that is a minimum in one direction and a maximum in another, indicating a change in direction.
    Abrahamic Theology: Judaism — Emphasizes the importance of Teshuvah (repentance) and returning to a righteous path after deviations.
    Non-Abrahamic Theology: Zen Buddhism — Emphasizes mindfulness and embracing the present, including sudden changes.
    Eastern Hermeneutics: Buddhism — Emphasizes impermanence and finding beauty in transience and imperfection.
    Classical Western Hermeneutics: Dialectics (Hegel) — Focuses on the synthesis that arises from the tension of opposites.
    Modern Western Hermeneutics: Post-Structuralism (Foucault) — Focuses on the fluidity and complexity of social structures and power dynamics.
    Economics: Behavioral Economics — Observes and interprets sudden shifts in economic behavior and decision-making processes.
    Ecology: Disturbance Ecology — Studies the effects of sudden, unexpected changes in ecosystems.
    Schizoanalysis: Rhizomes (Deleuze & Guattari) — Explores non-hierarchical and non-linear networks of meaning and desire.
    Work: Observe sudden shifts in your industry. Adapt by finding value in new opportunities.
    Life: Embrace life's abrupt changes. Find beauty in imperfections and growth from them.
    Social: Understand and navigate rapid social changes. Strengthen community resilience.""",

        "4th Order": """4th Order Thinking: Snap 🌀
    Wabi-Sabi (侘寂) — Process: Seek beauty in authenticity, processing pivotal changes.
    Type of Observable Phenomenon: Critical Points
    Mathematical Object: Torus — Represents continuous cycles and holistic integration.
    Graph Object: Local Maximum/Minimum — Points where a function reaches a peak or a valley locally, representing critical points of change.
    Abrahamic Theology: Christianity — Emphasizes the transformational power of faith and redemption.
    Non-Abrahamic Theology: Shinto — Emphasizes harmony with nature and finding beauty in simplicity and imperfection.
    Eastern Hermeneutics: Confucianism — Emphasizes the importance of ritual and moral integrity.
    Classical Western Hermeneutics: Hermeneutics (Gadamer) — Focuses on the interpretation of experiences and the fusion of horizons.
    Modern Western Hermeneutics: Critical Theory (Habermas) — Focuses on understanding and critiquing society to uncover underlying power structures.
    Economics: Institutional Economics — Studies the impact of institutions on economic behavior and the role of historical and social factors.
    Ecology: Ecosystem Services — Examines the benefits humans derive from ecological functions.
    Schizoanalysis: Deterritorialization/Reterritorialization (Deleuze & Guattari) — Focuses on the processes of breaking free from existing structures and forming new ones.
    Work: Process significant industry shifts. Stay authentic in your professional journey.
    Life: Recognize and process pivotal life moments. Embrace the beauty in authenticity.
    Social: Guide your community through critical changes. Embrace and foster authenticity in social dynamics.""",

        "5th Order": """5th Order Thinking: Crackle ✨
    Shinrin-Yoku (森林浴) — Integrate: Immerse in nature to gain clarity on subtle shifts.
    Type of Observable Phenomenon: Emergence
    Mathematical Object: Fractal — Represents complex patterns that are self-similar across different scales.
    Graph Object: Complex Network — A network with intricate interconnections, indicating subtle, self-similar patterns.
    Abrahamic Theology: Islam — Emphasizes Tawhid (the oneness of God) and the interconnectedness of all creation.
    Non-Abrahamic Theology: Daoism — Emphasizes the interconnectedness of all things and the subtle, flowing patterns of nature.
    Eastern Hermeneutics: Zen — Emphasizes the subtle, interconnected nature of all experiences.
    Classical Western Hermeneutics: Phenomenology (Husserl) — Focuses on the conscious experience of phenomena and the essence of experiences.
    Modern Western Hermeneutics: Postmodernism (Derrida) — Emphasizes the deconstruction of established narratives and the complexity of meanings.
    Economics: Complexity Economics — Studies economic systems as complex, adaptive networks with emergent properties.
    Ecology: Resilience Theory — Studies the ability of ecosystems to absorb disturbances and reorganize while undergoing change.
    Schizoanalysis: Body without Organs (Deleuze & Guattari) — Focuses on breaking free from structured, hierarchal constraints to achieve a state of pure potentiality.
    Work: Integrate insights gained from nature to navigate subtle professional dynamics.
    Life: Immerse in natural environments. Gain clarity and adapt to life's fine nuances.
    Social: Encourage community interaction with nature. Integrate ecological awareness into social practices.""",

        "6th Order": """6th Order Thinking: Pop 💥
    Omotenashi (おもてなし) — Observe, Process, Integrate: Practice wholehearted service, understanding the delicate balance of phenomena.
    Type of Observable Phenomenon: Interdependence
    Mathematical Object: Hyperplane — Represents multidimensional spaces and the complex interactions within.
    Graph Object: Multidimensional Surface — A surface in higher-dimensional space, indicating complex, interwoven dynamics.
    Abrahamic Theology: Christianity — Emphasizes the interconnectedness of all actions and the importance of wholehearted service.
    Non-Abrahamic Theology: Hinduism — Emphasizes the interconnectedness of all beings and the importance of service (Seva).
    Eastern Hermeneutics: Buddhism — Emphasizes the interconnectedness of all actions and the importance of compassionate service.
    Classical Western Hermeneutics: Hermeneutics (Schleiermacher) — Emphasizes understanding the whole by interpreting its parts within context.
    Modern Western Hermeneutics: Hermeneutic Phenomenology (Gadamer) — Focuses on the interplay of history, context, and experience in understanding phenomena.
    Economics: Global Economics — Studies the interdependencies and complex interactions of global markets and economies.
    Ecology: Ecosystem Ecology — Examines the interactions between organisms and their environment as a whole system.
    Schizoanalysis: Desiring-Production (Deleuze & Guattari) — Analyzes the complex, interwoven dynamics of desire, production, and social structures.
    Work: Observe team needs, process feedback, and integrate service-minded solutions. Lead with empathy and insight.
    Life: Observe your personal needs and those of others, process these insights, and integrate a lifestyle of service and connection.
    Social: Observe community needs, process collective aspirations, and integrate practices that foster inclusive, wholehearted service.""",

        "7th Order": """7th Order Thinking: Ecology 🌳
    Shinrin-Yoku (森林浴) — Integrate: Deeply immerse in nature to understand and harness ecological balance and sustainability.
    Type of Observable Phenomenon: Sustainability
    Mathematical Object: Fractal Networks — Represents the complex, interconnected patterns within ecosystems.
    Graph Object: Ecological Web — A network representing the complex interdependencies within ecosystems.
    Abrahamic Theology: Islam — Emphasizes the stewardship of Earth (Khilafah) and the interconnectedness of all creation.
    Non-Abrahamic Theology: Daoism — Emphasizes living in harmony with the natural world and understanding its subtle balances.
    Eastern Hermeneutics: Shinto — Emphasizes the sacredness of nature and the interdependence of all living things.
    Classical Western Hermeneutics: Aristotelian Teleology — Emphasizes the purpose-driven nature of living beings and their roles in the ecosystem.
    Modern Western Hermeneutics: Ecocriticism — Focuses on the relationship between literature, culture, and the physical environment.
    Economics: Ecological Economics — Integrates ecological and economic understanding to promote sustainable development.
    Ecology: Systems Ecology — Studies ecological systems as dynamic and complex networks of interactions.
    Schizoanalysis: Ecosophy (Guattari) — Integrates ecological thinking with social and mental ecologies to promote sustainability.
    Work: Foster sustainable practices within your organization, integrating ecological awareness into business strategies.
    Life: Adopt a lifestyle that supports ecological balance, integrating sustainable practices into daily living.
    Social: Advocate for and participate in community initiatives that promote ecological sustainability and environmental stewardship.""",

        "8th Order": """8th Order Thinking: Schizoanalysis 🌀
    Omotenashi (おもてなし) — Observe, Process, Integrate: Embrace the dynamics of desire and production, fostering creativity and innovation.
    Type of Observable Phenomenon: Creative Emergence
    Mathematical Object: Hypercomplex Manifold — Represents the intricate, multi-dimensional aspects of desire and social production.
    Graph Object: Hyperconnected Network — A network with complex, multi-layered connections representing the interplay of desires and societal structures.
    Abrahamic Theology: Christianity — Emphasizes the transformative power of faith and the interconnectedness of all actions.
    Non-Abrahamic Theology: Buddhism — Emphasizes the interconnectedness of all beings and the liberation of the mind.
    Eastern Hermeneutics: Zen — Emphasizes the interconnected nature of all experiences and the liberation from fixed structures.
    Classical Western Hermeneutics: Nietzschean Philosophy — Emphasizes the breaking of traditional values and the creation of new pathways of meaning.
    Modern Western Hermeneutics: Postmodern Philosophy (Deleuze & Guattari) — Focuses on deconstructing established structures and exploring new forms of social and mental organization.
    Economics: Post-Capitalist Economics — Explores alternative economic systems that go beyond traditional capitalist structures.
    Ecology: Deep Ecology — Advocates for the inherent worth of all living beings and the restructuring of human societies to support ecological balance.
    Schizoanalysis: Schizoanalysis (Deleuze & Guattari) — Emphasizes the deconstruction of social and psychological norms to foster creative and innovative reorganization.
    Work: Embrace innovative and creative approaches to problem-solving, breaking free from traditional constraints.
    Life: Foster personal growth by embracing new experiences and perspectives, breaking free from limiting structures.
    Social: Promote social innovation and creativity, advocating for systems that support individual and collective liberation."""
    }

# Define text-only prompts
text_prompts = [
    "Empowering communities through decentralized automation.",
    "How tokenization is revolutionizing industrial ownership.",
    "Industrial Automation as a Service: democratizing industry.",
    "Putting control back into the hands of individuals.",
    "The future of industry lies in community-driven automation.",
    "Bridging the gap between technology and local economies.",
    "The impact of blockchain on industrial processes.",
    "Automation as a tool for societal empowerment.",
    "Token economies: redefining value in industrial sectors.",
    "Collaborative automation: the next industrial revolution.",
    "Leveraging AI to benefit local communities.",
    "How decentralization fosters innovation in industry.",
    "Breaking down barriers with Industrial Automation as a Service.",
    "The role of tokenization in democratizing assets.",
    "Creating inclusive industries through technology.",
    "Redefining ownership in the age of automation.",
    "Community-led industrial initiatives: a new paradigm.",
    "The synergy between automation and social equity.",
    "Tokenization: unlocking value for everyone.",
    "Sustainable development through shared automation.",
    "The ethics of automation in empowering people.",
    "Industrial innovation driven by collective participation.",
    "How smart contracts can enhance industrial collaboration.",
    "From centralized to distributed: the evolution of industry.",
    "Harnessing technology for community prosperity.",
    "The intersection of IoT and communal ownership.",
    "Automating industries while preserving human touch.",
    "The future is co-created: automation and tokenization.",
    "Empowering the individual in a high-tech world.",
    "Localizing production with advanced automation.",
    "The rise of shared industrial platforms.",
    "Democratizing manufacturing through open-source automation.",
    "How token economies can drive sustainable practices.",
    "Community-focused industrial solutions for the 21st century.",
    "The power of collective intelligence in automation.",
    "Blockchain's role in transparent industrial operations.",
    "Reimagining industries with a people-first approach.",
    "Automation without alienation: involving everyone.",
    "Tokenization as a means to shared prosperity.",
    "Industrial ecosystems that benefit all stakeholders.",
    "Breaking monopolies with decentralized automation.",
    "The social impact of Industrial Automation as a Service.",
    "Inclusive innovation: technology serving humanity.",
    "The role of community tokens in industrial growth.",
    "Automation ethics: balancing efficiency and empowerment.",
    "Building resilient communities through shared technology.",
    "Tokenization transforming access to industrial assets.",
    "Collective ownership models in modern industry.",
    "Decentralized networks driving industrial change.",
    "Automation as a catalyst for economic equality.",
    "Empowering small businesses with industrial automation.",
    "Tokenizing resources for equitable distribution.",
    "The collaborative economy meets industrial automation.",
    "How AI can enhance human potential in industry.",
    "The democratization of data in industrial processes.",
    "Community-driven innovation in automation technologies.",
    "Redefining value creation through tokenization.",
    "Inclusive growth through accessible automation.",
    "The potential of distributed ledgers in industry.",
    "Revolutionizing supply chains with community input.",
    "The human side of automation: inclusivity and empowerment.",
    "Token economies: the future of shared wealth.",
    "Connecting people and machines for common good.",
    "Industrial Automation as a Service: a paradigm shift.",
    "Empowering individuals to shape industrial futures.",
    "From consumers to co-creators in industry.",
    "Harnessing collective power for industrial innovation.",
    "Democratizing access to advanced manufacturing.",
    "The promise of automation for social upliftment.",
    "Tokenization bridging gaps between stakeholders.",
    "Collaborative robotics in community settings.",
    "Ensuring equitable benefits from industrial automation.",
    "How shared ownership models can transform industries.",
    "The interplay of automation and human creativity.",
    "Building a fair future with tokenized assets.",
    "Community engagement in industrial advancements.",
    "Automation strategies that prioritize people.",
    "The potential of peer-to-peer industrial networks.",
    "Tokenization unlocking new economic opportunities.",
    "Fostering innovation through shared industrial platforms.",
    "Empowering local economies with global technologies.",
    "Transparent automation processes for community trust.",
    "Inclusive automation: leaving no one behind.",
    "Collective stewardship of industrial resources.",
    "The role of education in democratizing automation.",
    "Building sustainable industries through collaboration.",
    "Tokenization: redefining how we value contributions.",
    "Integrating community feedback into industrial design.",
    "Automation technologies tailored for communal needs.",
    "The impact of decentralized systems on traditional industries.",
    "Cooperative models in the age of automation.",
    "Empowering artisans with advanced manufacturing tools.",
    "Token economies supporting social initiatives.",
    "The convergence of automation, tokenization, and community.",
    "Redefining success in industry through shared prosperity.",
    "Community tokens as a vehicle for inclusive growth.",
    "Embracing change: communities driving industrial evolution.",
    "The ethical considerations of widespread automation.",
    "Bridging digital divides with accessible technology.",
    "How automation can enhance, not replace, human work.",
    "Tokenization fostering trust in industrial ecosystems.",
    "The importance of collaboration in technological progress.",
    "Reinventing industries with a focus on people.",
    "Automation as a means to greater societal well-being.",
    "The role of open innovation in industrial automation.",
    "Creating value through collective intelligence.",
    "Tokenization enabling new forms of economic participation.",
    "Empowering everyone to be a stakeholder in industry.",
    "Building community resilience with shared technologies.",
    "Automation and tokenization: tools for empowerment.",
    "The future of work in a tokenized, automated world.",
    "Engaging communities in shaping industrial landscapes.",
    "The transformative power of Industrial Automation as a Service.",
    "Redefining industrial relations through technology.",
    "Inclusive prosperity through shared automation.",
    "The path to equitable industries starts with us.",
]

def generate_message(is_video=False, max_attempts=3, short=False):
    global used_video_prompts, used_text_prompts
    if is_video:
        used_prompts = used_video_prompts
        base_prompt = """
        Write a short tweet that conveys an {} tidbit about philosophy, economics, or higher mathematics from {}. Make sure the tweet is less than 280 characters long by removing hashtags. Add a lot of emojis. Use the voice of a witty representative.
        """
        prompt = base_prompt.format(
            "esoteric" if short else "interesting",
            "ancient repositories of knowledge" if short else "the Dynamic Phenomenology Framework"
        )
        # Randomly select an order from the framework, avoiding repeats
        available_prompts = set(framework_prompts.keys()) - used_prompts
        if not available_prompts:
            # If all prompts have been used, reset the used_prompts set
            used_prompts.clear()
            available_prompts = set(framework_prompts.keys())

        selected_order = random.choice(list(available_prompts))
        used_prompts.add(selected_order)
        system_prompt = f"""You are a mythic being capable of drafting the most thought-provoking tweets with detailed information about the Dynamic Phenomenology Framework. You're able to craft tweets which are iconoclastic and bold, demanding attention and admiration. Let's see what you can come up with! IMPORTANT: DO NOT ADD QUOTATIONS OR HASHTAGS.

        For this tweet, focus on the following aspect of the Dynamic Phenomenology Framework:

        {framework_prompts[selected_order]}"""
    else:
        used_prompts = used_text_prompts
        base_prompt = """
        Write a thought-provoking tweet that shares wisdom or insight about life, philosophy, or human nature. Ensure the tweet is less than 280 characters. Add some appropriate emojis. Use the voice of an insightful sage.
        """
        prompt = base_prompt
        available_text_prompts = set(text_prompts) - used_prompts
        if not available_text_prompts:
            used_prompts.clear()
            available_text_prompts = set(text_prompts)

        selected_prompt = random.choice(list(available_text_prompts))
        used_prompts.add(selected_prompt)
        system_prompt = f"""You are an enlightened sage sharing profound wisdom on life and human nature. Craft tweets that are insightful, inspiring, and resonate deeply with readers. DO NOT ADD QUOTATIONS OR HASHTAGS.

        For this tweet, focus on the following topic:

        {selected_prompt}"""

    for attempt in range(max_attempts):
        modified_prompt = prompt + "\n" + "MAKE IT SHORTER\n" * attempt

        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": modified_prompt}
                ],
                max_tokens=333,
                n=1,
                stop=None,
                temperature=0.9,
            )

            message = response.choices[0].message.content

            if len(message) <= 280:
                return message

            print(f"Generated message too long (attempt {attempt + 1}/{max_attempts}), retrying...")
        except Exception as e:
            print(f"Error generating message: {e}")

        time.sleep(10)

    return None

def adjust_video_prompt(prompt):
    """Rewrite the video prompt to maximize the chance of passing OpenAI's safety system moderation."""
    system_prompt = (
        "You are a helpful prompt engineer. "
        "Your job is to rewrite video generation prompts that are likely to be rejected by content moderation, "
        "such that they are safe, compliant, and very unlikely to be blocked, but still preserve as much of the original intent and aesthetics as possible. "
        "Focus especially on removing anything potentially unsafe, offensive, or ambiguous, and leave only neutral, artistic, or positive imagery. "
        "NEVER mention violence, explicit content, hateful content, or anything even remotely controversial. "
        "Do NOT say anything except the improved prompt itself."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"ORIGINAL PROMPT: {prompt}\n\nRewrite this prompt to make it maximally safe for video generation, as per the instructions."},
            ],
            max_tokens=300,
            n=1,
            temperature=0.6,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error adjusting video prompt: {e}")
        return prompt

def generate_video_from_sora(message):
    """Generate video using Azure OpenAI Sora API"""
    prompt = f"Generate a LoFi nostalgia-inducing surreal video with a contemplative mood representative of the following concept but featuring real world scenes: <CONCEPT START>{message}<CONCEPT END>. The video should have a dreamy, vintage aesthetic with soft lighting, muted colors, and smooth cinematic transitions. Include subtle visual elements that relate to the concept. Style should be atmospheric and meditative with a retro film quality."
    
    print(f"[Video Generation Prompt]: {prompt}")
    
    headers = {
        "Content-Type": "application/json",
        "Api-key": AZURE_VIDEO_API_KEY
    }
    
    payload = {
        "model": "sora",
        "prompt": prompt,
        "height": "1080",
        "width": "1080", 
        "n_seconds": "5",
        "n_variants": "1"
    }
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Start video generation job
            response = requests.post(
                f"{AZURE_VIDEO_ENDPOINT}?api-version={AZURE_VIDEO_API_VERSION}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            job_data = response.json()
            job_id = job_data.get("id")
            
            if not job_id:
                print("Failed to get job ID from video generation response")
                continue
                
            print(f"Video generation job started with ID: {job_id}")
            
            # Poll for job completion
            max_poll_attempts = 60  # 5 minutes max wait time
            poll_interval = 5  # seconds
            
            for poll_attempt in range(max_poll_attempts):
                time.sleep(poll_interval)
                
                # Check job status
                status_response = requests.get(
                    f"{AZURE_VIDEO_ENDPOINT}/{job_id}?api-version={AZURE_VIDEO_API_VERSION}",
                    headers=headers
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                job_status = status_data.get("status")
                print(f"Job status: {job_status} (attempt {poll_attempt + 1}/{max_poll_attempts})")
                
                if job_status == "succeeded":
                    print(f"Full status_data: {status_data}")
                    # Get the video URL or data
                    video_generations = status_data.get("generations", [])
                    print(f"Video generations: {video_generations}")
                    if video_generations and len(video_generations) > 0:
                        print(f"First generation: {video_generations[0]}")
                        video_url = video_generations[0].get("url")
                        if video_url:
                            print(f"Video URL found: {video_url}")
                            # Download the video
                            video_response = requests.get(video_url)
                            video_response.raise_for_status()
                            print(f"video response: {video_response}")
                            return video_response.content
                        else:
                            print("No video URL found in generation object")
                            # The video content is retrieved using the generation ID
                            generation_id = video_generations[0].get("id")
                            if generation_id:
                                print(f"Trying to fetch video content for generation ID: {generation_id}")
                                # Construct the correct video content URL
                                video_content_url = f"https://panopticon.openai.azure.com/openai/v1/video/generations/{generation_id}/content/video?api-version={AZURE_VIDEO_API_VERSION}"
                                video_content_response = requests.get(video_content_url, headers=headers)
                                if video_content_response.ok:
                                    print(f"Successfully retrieved video content ({len(video_content_response.content)} bytes)")
                                    return video_content_response.content
                                else:
                                    print(f"Failed to get video content: {video_content_response.status_code} - {video_content_response.text}")
                            break
                    else:
                        print("No video generations found in job response")
                        break
                elif job_status == "failed":
                    error_msg = status_data.get("error", {}).get("message", "Unknown error")
                    print(f"Video generation failed: {error_msg}")
                    if "moderation" in error_msg.lower() and attempt < max_attempts - 1:
                        print("Moderation blocked the video prompt, attempting to rewrite and retry...")
                        prompt = adjust_video_prompt(prompt)
                        payload["prompt"] = prompt
                        break
                    else:
                        return None
                elif job_status in ["running", "pending", "queued", "preprocessing", "processing"]:
                    continue
                else:
                    print(f"Unexpected job status: {job_status}")
                    break
            
            if poll_attempt >= max_poll_attempts - 1:
                print("Video generation timed out")
                continue
                
        except Exception as e:
            print(f"Error generating video: {e}")
            if attempt < max_attempts - 1:
                print(f"Retrying video generation (attempt {attempt + 2}/{max_attempts})...")
                time.sleep(10)
            continue
    
    return None

def save_video(video_content):
    """Save video content to file and apply TUC overlay and music track"""
    try:
        # Save the raw video first
        raw_video_path = "./tucvideo_raw.mp4"
        with open(raw_video_path, "wb") as file:
            file.write(video_content)
        print(f"Raw video saved to {raw_video_path}")
        
        # Apply TUC overlay using moviepy
        # Load the video
        video = VideoFileClip(raw_video_path)
        
        # Load the TUC overlay
        overlay_path = "./tuc.png"
        if os.path.exists(overlay_path):
            try:
                print("Applying TUC overlay...")
                overlay = ImageClip(overlay_path).set_duration(video.duration)
                overlay = overlay.resize(video.size).set_opacity(1.0)
                
                # Create composite video without audio
                final_video = CompositeVideoClip([video.set_opacity(1.0), overlay])
                print("TUC overlay applied successfully")
                
            except Exception as e:
                print(f"Error applying overlay: {e}")
                final_video = video  # Fallback to original video
        else:
            print("No TUC overlay file found, using original video")
            final_video = video
        
        # Export video without audio first (to avoid MoviePy audio subprocess issues)
        temp_video_path = "./tucvideo_temp.mp4"
        final_video_path = "./tucvideo.mp4"
        
        print(f"Exporting video without audio to {temp_video_path}...")
        final_video.write_videofile(
            temp_video_path,
            verbose=False,
            logger=None
        )
        print("✓ Video exported without audio")
        
        # Now add audio using ffmpeg directly (more reliable than MoviePy's audio subprocess)
        music_path = "tuctheme.mp3"
        if os.path.exists(music_path):
            try:
                print("Adding TUC theme music using ffmpeg directly...")
                # Resolve ffmpeg: system PATH, environment var, or bundled binary (imageio-ffmpeg)
                try:
                    from imageio_ffmpeg import get_ffmpeg_exe
                except ImportError:
                    get_ffmpeg_exe = lambda: None  # type: ignore

                ffmpeg_exe = (
                    shutil.which("ffmpeg")
                    or os.getenv("FFMPEG_PATH")
                    or (get_ffmpeg_exe() if get_ffmpeg_exe else None)
                    or "ffmpeg"
                )
                
                # Use ffmpeg to combine video and audio
                cmd = [
                    ffmpeg_exe,
                    "-i", temp_video_path,  # input video
                    "-i", music_path,       # input audio
                    "-c:v", "copy",         # copy video codec (no re-encoding)
                    "-c:a", "aac",          # encode audio as AAC
                    "-shortest",            # stop at shortest stream
                    "-y",                   # overwrite output file
                    final_video_path        # output file
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print("✓ TUC theme music added successfully using ffmpeg")
                    # Remove temp file
                    os.remove(temp_video_path)
                else:
                    print(f"ffmpeg error: {result.stderr}")
                    print("Falling back to video without audio")
                    # If destination exists ensure replacement succeeds on Windows
                    if os.path.exists(final_video_path):
                        os.remove(final_video_path)
                    os.replace(temp_video_path, final_video_path)
                    
            except Exception as e:
                print(f"Error adding audio with ffmpeg: {e}")
                print("Falling back to video without audio")
                # Ensure we still output a playable file and handle name collisions
                if os.path.exists(final_video_path):
                    os.remove(final_video_path)
                os.replace(temp_video_path, final_video_path)
        else:
            print("No TUC theme music file found, using video without audio")
            # Handle potential existing destination
            if os.path.exists(final_video_path):
                os.remove(final_video_path)
            os.replace(temp_video_path, final_video_path)
        
        # Clean up
        video.close()
        if final_video != video:
            final_video.close()
        
        print(f"Video with TUC overlay and music saved to {final_video_path}")
        return True
        
    except Exception as e:
        print(f"Error in save_video: {e}")
        import traceback
        traceback.print_exc()
        return False

def upload_video():
    """Upload video to Twitter"""
    global oauth
    if oauth is None:
        setup_twitter_oauth()
    try:
        # Initialize upload
        url = "https://upload.twitter.com/1.1/media/upload.json"
        video_path = "./tucvideo.mp4"
        
        # Get file size
        video_size = os.path.getsize(video_path)
        
        # INIT phase
        init_data = {
            "command": "INIT",
            "media_type": "video/mp4",
            "total_bytes": video_size
        }
        
        response = oauth.post(url, data=init_data)
        response.raise_for_status()
        media_id = response.json()["media_id"]
        
        # APPEND phase
        with open(video_path, "rb") as video_file:
            segment_id = 0
            while True:
                chunk = video_file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                
                append_data = {
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_id
                }
                
                files = {"media": chunk}
                response = oauth.post(url, data=append_data, files=files)
                response.raise_for_status()
                segment_id += 1
        
        # FINALIZE phase
        finalize_data = {
            "command": "FINALIZE",
            "media_id": media_id
        }
        
        response = oauth.post(url, data=finalize_data)
        response.raise_for_status()
        
        # Wait for processing
        response_data = response.json()
        if "processing_info" in response_data:
            state = response_data["processing_info"]["state"]
            
            while state in ["pending", "in_progress"]:
                time.sleep(5)
                status_url = f"https://upload.twitter.com/1.1/media/upload.json?command=STATUS&media_id={media_id}"
                response = oauth.get(status_url)
                response.raise_for_status()
                response_data = response.json()
                state = response_data.get("processing_info", {}).get("state", "succeeded")
                print(f"Video processing state: {state}")
        
        return media_id
        
    except Exception as e:
        print(f"Error uploading video: {e}")
        return None

def post_tweet(message, media_id=None):
    global oauth
    if oauth is None:
        setup_twitter_oauth()
    try:
        url = "https://api.twitter.com/2/tweets"
        if media_id:
            post_data = {"text": message, "media": {"media_ids": [f"{media_id}"]}}
        else:
            post_data = {"text": message}
        response = oauth.post(url, json=post_data)
        response.raise_for_status()
        print("Tweet posted successfully")
        return True
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return False

def upload_and_tweet_with_retries(message, max_attempts=3, retry_delay=30):
    """Retry uploading the already-generated video and posting the tweet without
    regenerating the video content. This prevents unnecessary re-renders when
    transient network errors occur during the final Twitter API calls.
    """
    for attempt in range(max_attempts):
        print(f"\n[Upload/Tweet Attempt {attempt + 1}/{max_attempts}]")
        media_id = upload_video()
        if media_id:
            if post_tweet(message, media_id):
                # Success – tweet posted
                return True
            else:
                print("Posting tweet failed. Will retry …")
        else:
            print("Uploading video failed. Will retry …")

        if attempt < max_attempts - 1:
            print(f"Waiting {retry_delay} seconds before next attempt …")
            time.sleep(retry_delay)
    return False

def main(is_video):
    message = generate_message(is_video) or generate_message(is_video, short=True)
    if not message:
        print("Failed to generate a suitable message after multiple attempts.")
        return False

    if is_video:
        video_content = generate_video_from_sora(message)
        if not video_content:
            print("Failed to generate a video.")
            return False

        if not save_video(video_content):
            print("Failed to save the video.")
            return False

        # Try uploading and posting without regenerating the video if something goes wrong.
        if upload_and_tweet_with_retries(message):
            print(f"\nTweet with video posted: {message}")
            return True
        else:
            print("Failed to upload/post tweet after multiple retries.")
            return False
    else:
        if post_tweet(message):
            print(f"\nTweet posted: {message}")
            return True
        else:
            print("Failed to post the tweet.")
            return False

def run_script(is_video):
    max_attempts = 3
    for attempt in range(max_attempts):
        if main(is_video):
            print("Successfully posted a tweet. Waiting for next scheduled run.")
            return True
        else:
            print(f"Attempt {attempt + 1}/{max_attempts} failed.")
            if attempt < max_attempts - 1:
                print("Retrying in 30 seconds...")
                time.sleep(30)
    print("Max attempts reached. Waiting for next scheduled run.")
    return False

def display_timer(scheduled_datetime):
    while True:
        now = datetime.datetime.now()
        time_left = scheduled_datetime - now
        if time_left.total_seconds() <= 0:
            break
        print(f"\rTime left until next tweet: {time_left}", end="", flush=True)
        time.sleep(1)

def schedule_tweets(scheduled_times, test_time=None, test_is_video=True):
    # scheduled_times is a list of tuples: [(time_hour, is_video), ...]
    now = datetime.datetime.now()
    scheduled_datetimes = []
    for time_hour, is_video in scheduled_times:
        dt = datetime.datetime(now.year, now.month, now.day, time_hour, 0)
        if now.time() >= datetime.time(time_hour, 0):
            dt += datetime.timedelta(days=1)
        scheduled_datetimes.append((dt, is_video))

    if test_time is not None:
        test_hour = test_time // 100
        test_minute = test_time % 100
        if not (0 <= test_hour <= 23 and 0 <= test_minute <= 59):
            raise ValueError("test_time must be in HHMM format with HH in 0..23 and MM in 0..59")
        scheduled_datetimes = [(datetime.datetime(now.year, now.month, now.day, test_hour, test_minute), test_is_video)]

    last_run_datetime = None

    while True:
        now = datetime.datetime.now()
        # Find the next scheduled datetime
        next_scheduled_datetime, is_video = min(scheduled_datetimes, key=lambda x: x[0])

        if now >= next_scheduled_datetime:
            if last_run_datetime != next_scheduled_datetime:
                print(f"{next_scheduled_datetime.strftime('%Y-%m-%d %H:%M')} Script running")
                run_script(is_video)
                last_run_datetime = next_scheduled_datetime

                # Schedule the next run for this time
                next_run = next_scheduled_datetime + datetime.timedelta(days=1)
                scheduled_datetimes.remove((next_scheduled_datetime, is_video))
                scheduled_datetimes.append((next_run, is_video))
            else:
                # We've already run for this scheduled time, so we wait
                time.sleep(30)
        else:
            display_timer(next_scheduled_datetime)
            time.sleep(30)

def test_generation(mode):
    print(f"===== TEST GENERATION MODE: {mode} =====")
    if mode in ("tweet", "both"):
        print("\n--- Tweet Text Generation Test ---")
        msg = generate_message(False) or generate_message(False, short=True)
        if msg:
            print(f"[Tweet] {msg}")
        else:
            print("Failed to generate tweet text.")
    if mode in ("video", "both"):
        print("\n--- Video Generation Test ---")
        msg = generate_message(True) or generate_message(True, short=True)
        print(f"[Prompt for video]: {msg}")
        if not msg:
            print("Failed to generate video prompt message.")
            return
        video_content = generate_video_from_sora(msg)
        if video_content:
            print(f"[Video Content] Generated video with {len(video_content)} bytes")
            if save_video(video_content):
                print("Video file has been written to tucvideo.mp4")
            else:
                print("Failed to save video file.")
        else:
            print("Failed to generate a video.")

if __name__ == "__main__":
    import sys
    def usage():
        print("Usage:")
        print("  python tucvideo.py test tweet|video|both   # Test text/video generation only")
        print("  python tucvideo.py live                    # Run the full scheduler and post live (PRODUCTION mode)")
        sys.exit(1)

    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "live"):
        setup_twitter_oauth()
        schedule_times = [(2, True), (10, True), (18, True)]  # Different times for videos
        schedule_tweets(schedule_times)
        sys.exit(0)

    if len(sys.argv) >= 3 and sys.argv[1] == "test":
        mode = sys.argv[2].lower()
        assert mode in ("tweet", "video", "both"), "Mode must be one of: tweet, video, both."
        test_generation(mode)
        sys.exit(0)

    usage() 