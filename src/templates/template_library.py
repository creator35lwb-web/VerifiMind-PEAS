"""
Template Library
Pre-built templates for common application types
Each template includes database schema, API structure, UI pages, and deployment config
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class AppTemplate:
    """Represents a complete application template"""
    id: str
    name: str
    category: str
    description: str

    # Technology stack
    tech_stack: Dict[str, str]

    # Database entities
    entities: List[Dict[str, Any]]

    # API endpoints
    api_endpoints: List[Dict[str, Any]]

    # UI pages/screens
    ui_pages: List[Dict[str, Any]]

    # Built-in features
    features: List[str]

    # Compliance requirements
    compliance_features: List[str] = field(default_factory=list)

    # Security features
    security_features: List[str] = field(default_factory=list)

    # Recommended deployment
    recommended_deployment: str = 'vercel'

    # Customization points
    customizable_aspects: List[str] = field(default_factory=list)


class TemplateLibrary:
    """
    Central repository of all application templates
    """

    def __init__(self):
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, AppTemplate]:
        """Initialize all available templates"""
        return {
            'fitness_tracker': self._create_fitness_tracker_template(),
            'meditation_app': self._create_meditation_app_template(),
            'todo_list': self._create_todo_list_template(),
            'social_network': self._create_social_network_template(),
            'ecommerce': self._create_ecommerce_template(),
            'blog_platform': self._create_blog_platform_template(),
            'education_platform': self._create_education_platform_template(),
        }

    def get_template(self, template_id: str) -> AppTemplate:
        """Retrieves a template by ID"""
        return self.templates.get(template_id)

    def find_best_template(self, category: str, keywords: List[str]) -> AppTemplate:
        """Finds the best matching template based on category and keywords"""
        # Match by category first
        category_matches = [
            t for t in self.templates.values()
            if t.category.lower() == category.lower()
        ]

        if category_matches:
            return category_matches[0]

        # Fallback to basic CRUD template
        return self.templates.get('todo_list')

    def _create_fitness_tracker_template(self) -> AppTemplate:
        """Fitness & wellness tracking application"""
        return AppTemplate(
            id='fitness_tracker',
            name='Fitness Tracker',
            category='Health & Fitness',
            description='Track workouts, nutrition, and health metrics',
            tech_stack={
                'backend': 'Node.js + Express',
                'frontend': 'React + TypeScript',
                'database': 'PostgreSQL',
                'auth': 'JWT',
                'deployment': 'Vercel + Railway'
            },
            entities=[
                {
                    'name': 'User',
                    'description': 'Application users',
                    'fields': [
                        {'name': 'email', 'type': 'email', 'required': True, 'unique': True},
                        {'name': 'password_hash', 'type': 'string', 'required': True},
                        {'name': 'name', 'type': 'string', 'required': True},
                        {'name': 'age', 'type': 'integer'},
                        {'name': 'weight', 'type': 'float'},
                        {'name': 'height', 'type': 'float'},
                        {'name': 'fitness_goals', 'type': 'json'},
                    ]
                },
                {
                    'name': 'Workout',
                    'description': 'Workout sessions',
                    'fields': [
                        {'name': 'user_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                        {'name': 'workout_type', 'type': 'string', 'required': True},
                        {'name': 'duration_minutes', 'type': 'integer', 'required': True},
                        {'name': 'calories_burned', 'type': 'integer'},
                        {'name': 'notes', 'type': 'text'},
                        {'name': 'date', 'type': 'date', 'required': True, 'indexed': True},
                    ]
                },
                {
                    'name': 'Meal',
                    'description': 'Nutrition tracking',
                    'fields': [
                        {'name': 'user_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                        {'name': 'meal_type', 'type': 'string', 'required': True},
                        {'name': 'description', 'type': 'text', 'required': True},
                        {'name': 'calories', 'type': 'integer'},
                        {'name': 'protein_g', 'type': 'float'},
                        {'name': 'carbs_g', 'type': 'float'},
                        {'name': 'fat_g', 'type': 'float'},
                        {'name': 'date', 'type': 'date', 'required': True, 'indexed': True},
                    ]
                },
                {
                    'name': 'HealthMetric',
                    'description': 'Health measurements over time',
                    'fields': [
                        {'name': 'user_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                        {'name': 'metric_type', 'type': 'string', 'required': True},
                        {'name': 'value', 'type': 'float', 'required': True},
                        {'name': 'unit', 'type': 'string', 'required': True},
                        {'name': 'date', 'type': 'date', 'required': True, 'indexed': True},
                    ]
                }
            ],
            api_endpoints=[
                {'method': 'POST', 'path': '/api/auth/register', 'description': 'User registration'},
                {'method': 'POST', 'path': '/api/auth/login', 'description': 'User login'},
                {'method': 'GET', 'path': '/api/workouts', 'description': 'List user workouts'},
                {'method': 'POST', 'path': '/api/workouts', 'description': 'Log a workout'},
                {'method': 'GET', 'path': '/api/meals', 'description': 'List user meals'},
                {'method': 'POST', 'path': '/api/meals', 'description': 'Log a meal'},
                {'method': 'GET', 'path': '/api/health-metrics', 'description': 'Get health metrics'},
                {'method': 'POST', 'path': '/api/health-metrics', 'description': 'Record health metric'},
                {'method': 'GET', 'path': '/api/dashboard', 'description': 'Get dashboard summary'},
            ],
            ui_pages=[
                {
                    'name': 'Dashboard',
                    'route': '/',
                    'description': 'Overview of fitness progress',
                    'components': ['StatsCards', 'WorkoutChart', 'NutritionSummary']
                },
                {
                    'name': 'Workouts',
                    'route': '/workouts',
                    'description': 'Workout history and logging',
                    'components': ['WorkoutList', 'WorkoutForm', 'WorkoutCalendar']
                },
                {
                    'name': 'Nutrition',
                    'route': '/nutrition',
                    'description': 'Meal tracking and nutrition',
                    'components': ['MealList', 'MealForm', 'CalorieChart']
                },
                {
                    'name': 'Profile',
                    'route': '/profile',
                    'description': 'User profile and settings',
                    'components': ['ProfileForm', 'GoalsEditor']
                },
            ],
            features=[
                'User authentication',
                'Workout logging',
                'Nutrition tracking',
                'Progress visualization',
                'Health metrics tracking',
                'Dashboard analytics',
            ],
            compliance_features=[
                'GDPR data export',
                'Privacy policy',
                'Terms of service',
                'Cookie consent',
            ],
            security_features=[
                'Password hashing (bcrypt)',
                'JWT authentication',
                'Rate limiting',
                'Input validation',
                'XSS protection',
            ],
            customizable_aspects=[
                'Workout types',
                'Meal categories',
                'Health metrics tracked',
                'Color scheme',
                'Dashboard layout',
            ]
        )

    def _create_meditation_app_template(self) -> AppTemplate:
        """Meditation & mindfulness app (especially for children)"""
        return AppTemplate(
            id='meditation_app',
            name='Meditation App',
            category='Health & Wellness',
            description='Guided meditation and mindfulness exercises',
            tech_stack={
                'backend': 'Node.js + Express',
                'frontend': 'React + TypeScript',
                'database': 'PostgreSQL',
                'auth': 'JWT',
                'deployment': 'Vercel + Railway'
            },
            entities=[
                {
                    'name': 'Parent',
                    'description': 'Parent accounts',
                    'fields': [
                        {'name': 'email', 'type': 'email', 'required': True, 'unique': True},
                        {'name': 'password_hash', 'type': 'string', 'required': True},
                        {'name': 'name', 'type': 'string', 'required': True},
                        {'name': 'verified', 'type': 'boolean', 'default': 'false'},
                    ]
                },
                {
                    'name': 'Child',
                    'description': 'Child profiles',
                    'fields': [
                        {'name': 'parent_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'parents'}},
                        {'name': 'name', 'type': 'string', 'required': True},
                        {'name': 'age', 'type': 'integer', 'required': True},
                        {'name': 'avatar', 'type': 'string'},
                        {'name': 'daily_limit_minutes', 'type': 'integer', 'default': '15'},
                    ]
                },
                {
                    'name': 'MeditationSession',
                    'description': 'Completed meditation sessions',
                    'fields': [
                        {'name': 'child_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'children'}},
                        {'name': 'exercise_id', 'type': 'string', 'required': True},
                        {'name': 'duration_seconds', 'type': 'integer', 'required': True},
                        {'name': 'completed', 'type': 'boolean', 'default': 'true'},
                        {'name': 'mood_before', 'type': 'string'},
                        {'name': 'mood_after', 'type': 'string'},
                        {'name': 'date', 'type': 'date', 'required': True, 'indexed': True},
                    ]
                },
                {
                    'name': 'Exercise',
                    'description': 'Meditation exercises library',
                    'fields': [
                        {'name': 'title', 'type': 'string', 'required': True},
                        {'name': 'description', 'type': 'text', 'required': True},
                        {'name': 'duration_seconds', 'type': 'integer', 'required': True},
                        {'name': 'age_min', 'type': 'integer', 'default': '6'},
                        {'name': 'age_max', 'type': 'integer', 'default': '12'},
                        {'name': 'category', 'type': 'string', 'required': True},
                        {'name': 'audio_url', 'type': 'url'},
                        {'name': 'video_url', 'type': 'url'},
                    ]
                },
                {
                    'name': 'UsageLog',
                    'description': 'Daily usage tracking for screen time limits',
                    'fields': [
                        {'name': 'child_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'children'}},
                        {'name': 'date', 'type': 'date', 'required': True, 'indexed': True},
                        {'name': 'total_minutes', 'type': 'integer', 'default': '0'},
                    ]
                }
            ],
            api_endpoints=[
                {'method': 'POST', 'path': '/api/auth/parent/register', 'description': 'Parent registration with consent'},
                {'method': 'POST', 'path': '/api/auth/parent/login', 'description': 'Parent login'},
                {'method': 'POST', 'path': '/api/children', 'description': 'Create child profile'},
                {'method': 'GET', 'path': '/api/children', 'description': 'List children for parent'},
                {'method': 'GET', 'path': '/api/exercises', 'description': 'List age-appropriate exercises'},
                {'method': 'POST', 'path': '/api/sessions', 'description': 'Log meditation session'},
                {'method': 'GET', 'path': '/api/sessions', 'description': 'Get session history'},
                {'method': 'GET', 'path': '/api/parent/dashboard', 'description': 'Parent dashboard with child progress'},
                {'method': 'GET', 'path': '/api/usage/today', 'description': 'Check today\'s screen time usage'},
            ],
            ui_pages=[
                {
                    'name': 'ParentDashboard',
                    'route': '/parent',
                    'description': 'Parent monitoring dashboard',
                    'components': ['ChildSelector', 'ProgressCharts', 'UsageReport', 'SettingsPanel']
                },
                {
                    'name': 'ChildHome',
                    'route': '/child',
                    'description': 'Child-friendly home screen',
                    'components': ['WelcomeMessage', 'ExerciseGrid', 'MoodTracker']
                },
                {
                    'name': 'ExercisePlayer',
                    'route': '/exercise/:id',
                    'description': 'Meditation exercise player',
                    'components': ['VideoPlayer', 'AudioPlayer', 'BreathingAnimation', 'Timer']
                },
                {
                    'name': 'Progress',
                    'route': '/progress',
                    'description': 'Child progress and achievements',
                    'components': ['StreakCounter', 'BadgeDisplay', 'ProgressChart']
                },
            ],
            features=[
                'Parental consent system',
                'Age verification',
                'Child profiles with avatars',
                'Screen time limits (15 min/day default)',
                'Age-appropriate content filtering',
                'Guided breathing exercises',
                'Mood tracking (before/after)',
                'Parent dashboard',
                'Progress tracking',
                'Achievements & badges',
            ],
            compliance_features=[
                'COPPA compliance',
                'Parental consent required',
                'No data collection from children',
                'Privacy policy (child-focused)',
                'Age-appropriate content only',
                'Screen time enforcement',
                'Parental controls',
            ],
            security_features=[
                'Separate parent/child authentication',
                'Age verification',
                'Encrypted data storage',
                'No third-party tracking',
                'Content moderation',
            ],
            customizable_aspects=[
                'Daily time limits',
                'Exercise library',
                'Age ranges',
                'Mood options',
                'Reward system',
                'Color scheme (calming)',
            ]
        )

    def _create_todo_list_template(self) -> AppTemplate:
        """Basic CRUD todo list application"""
        return AppTemplate(
            id='todo_list',
            name='Todo List',
            category='Productivity',
            description='Task management and todo tracking',
            tech_stack={
                'backend': 'Node.js + Express',
                'frontend': 'React',
                'database': 'PostgreSQL',
                'auth': 'JWT',
                'deployment': 'Vercel'
            },
            entities=[
                {
                    'name': 'User',
                    'fields': [
                        {'name': 'email', 'type': 'email', 'required': True, 'unique': True},
                        {'name': 'password_hash', 'type': 'string', 'required': True},
                        {'name': 'name', 'type': 'string', 'required': True},
                    ]
                },
                {
                    'name': 'Task',
                    'fields': [
                        {'name': 'user_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                        {'name': 'title', 'type': 'string', 'required': True},
                        {'name': 'description', 'type': 'text'},
                        {'name': 'completed', 'type': 'boolean', 'default': 'false'},
                        {'name': 'due_date', 'type': 'date'},
                        {'name': 'priority', 'type': 'string', 'default': "'medium'"},
                    ]
                }
            ],
            api_endpoints=[
                {'method': 'POST', 'path': '/api/auth/register', 'description': 'Register'},
                {'method': 'POST', 'path': '/api/auth/login', 'description': 'Login'},
                {'method': 'GET', 'path': '/api/tasks', 'description': 'List tasks'},
                {'method': 'POST', 'path': '/api/tasks', 'description': 'Create task'},
                {'method': 'PUT', 'path': '/api/tasks/:id', 'description': 'Update task'},
                {'method': 'DELETE', 'path': '/api/tasks/:id', 'description': 'Delete task'},
            ],
            ui_pages=[
                {'name': 'TaskList', 'route': '/', 'components': ['TaskList', 'TaskForm']},
                {'name': 'Profile', 'route': '/profile', 'components': ['ProfileForm']},
            ],
            features=['User auth', 'Task CRUD', 'Task filtering', 'Due dates'],
            compliance_features=['Privacy policy', 'Data export'],
            security_features=['JWT auth', 'Password hashing', 'Input validation'],
        )

    def _create_social_network_template(self) -> AppTemplate:
        """Social networking platform"""
        return AppTemplate(
            id='social_network',
            name='Social Network',
            category='Social',
            description='Social networking with posts, followers, and messaging',
            tech_stack={
                'backend': 'Node.js + Express',
                'frontend': 'React + TypeScript',
                'database': 'PostgreSQL',
                'auth': 'JWT',
                'realtime': 'Socket.io',
                'deployment': 'AWS'
            },
            entities=[
                {
                    'name': 'User',
                    'fields': [
                        {'name': 'username', 'type': 'string', 'required': True, 'unique': True},
                        {'name': 'email', 'type': 'email', 'required': True, 'unique': True},
                        {'name': 'password_hash', 'type': 'string', 'required': True},
                        {'name': 'bio', 'type': 'text'},
                        {'name': 'avatar_url', 'type': 'url'},
                        {'name': 'verified', 'type': 'boolean', 'default': 'false'},
                    ]
                },
                {
                    'name': 'Post',
                    'fields': [
                        {'name': 'user_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                        {'name': 'content', 'type': 'text', 'required': True},
                        {'name': 'media_urls', 'type': 'json'},
                        {'name': 'likes_count', 'type': 'integer', 'default': '0'},
                        {'name': 'comments_count', 'type': 'integer', 'default': '0'},
                    ]
                },
                {
                    'name': 'Follow',
                    'fields': [
                        {'name': 'follower_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                        {'name': 'following_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                    ]
                },
                {
                    'name': 'Comment',
                    'fields': [
                        {'name': 'post_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'posts'}},
                        {'name': 'user_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                        {'name': 'content', 'type': 'text', 'required': True},
                    ]
                },
                {
                    'name': 'Like',
                    'fields': [
                        {'name': 'post_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'posts'}},
                        {'name': 'user_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                    ]
                }
            ],
            api_endpoints=[
                {'method': 'POST', 'path': '/api/auth/register', 'description': 'Register'},
                {'method': 'POST', 'path': '/api/auth/login', 'description': 'Login'},
                {'method': 'GET', 'path': '/api/feed', 'description': 'Get personalized feed'},
                {'method': 'POST', 'path': '/api/posts', 'description': 'Create post'},
                {'method': 'POST', 'path': '/api/posts/:id/like', 'description': 'Like post'},
                {'method': 'POST', 'path': '/api/posts/:id/comment', 'description': 'Comment on post'},
                {'method': 'POST', 'path': '/api/users/:id/follow', 'description': 'Follow user'},
                {'method': 'GET', 'path': '/api/users/:id', 'description': 'Get user profile'},
            ],
            ui_pages=[
                {'name': 'Feed', 'route': '/', 'components': ['PostFeed', 'CreatePost']},
                {'name': 'Profile', 'route': '/profile/:username', 'components': ['ProfileHeader', 'PostGrid']},
                {'name': 'Explore', 'route': '/explore', 'components': ['TrendingPosts', 'SuggestedUsers']},
            ],
            features=['User profiles', 'Posts', 'Likes', 'Comments', 'Follow system', 'Feed algorithm'],
            compliance_features=['Content moderation', 'Report system', 'Privacy settings', 'Block users'],
            security_features=['Content filtering', 'Rate limiting', 'Spam detection', 'Account verification'],
        )

    def _create_ecommerce_template(self) -> AppTemplate:
        """E-commerce platform"""
        return AppTemplate(
            id='ecommerce',
            name='E-commerce Store',
            category='E-commerce',
            description='Online store with products, cart, and checkout',
            tech_stack={
                'backend': 'Node.js + Express',
                'frontend': 'React + TypeScript',
                'database': 'PostgreSQL',
                'payment': 'Stripe',
                'deployment': 'AWS'
            },
            entities=[
                {'name': 'User', 'fields': [
                    {'name': 'email', 'type': 'email', 'required': True, 'unique': True},
                    {'name': 'password_hash', 'type': 'string', 'required': True},
                    {'name': 'name', 'type': 'string', 'required': True},
                    {'name': 'shipping_address', 'type': 'json'},
                ]},
                {'name': 'Product', 'fields': [
                    {'name': 'name', 'type': 'string', 'required': True},
                    {'name': 'description', 'type': 'text', 'required': True},
                    {'name': 'price', 'type': 'float', 'required': True},
                    {'name': 'stock', 'type': 'integer', 'default': '0'},
                    {'name': 'images', 'type': 'json'},
                    {'name': 'category', 'type': 'string'},
                ]},
                {'name': 'Order', 'fields': [
                    {'name': 'user_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                    {'name': 'status', 'type': 'string', 'default': "'pending'"},
                    {'name': 'total', 'type': 'float', 'required': True},
                    {'name': 'items', 'type': 'json', 'required': True},
                    {'name': 'shipping_address', 'type': 'json', 'required': True},
                ]},
            ],
            api_endpoints=[
                {'method': 'GET', 'path': '/api/products', 'description': 'List products'},
                {'method': 'GET', 'path': '/api/products/:id', 'description': 'Get product'},
                {'method': 'POST', 'path': '/api/cart', 'description': 'Add to cart'},
                {'method': 'POST', 'path': '/api/checkout', 'description': 'Create order'},
                {'method': 'POST', 'path': '/api/payment', 'description': 'Process payment'},
            ],
            ui_pages=[
                {'name': 'Home', 'route': '/', 'components': ['ProductGrid', 'FeaturedProducts']},
                {'name': 'Product', 'route': '/product/:id', 'components': ['ProductDetails', 'AddToCart']},
                {'name': 'Cart', 'route': '/cart', 'components': ['CartItems', 'Checkout']},
                {'name': 'Checkout', 'route': '/checkout', 'components': ['PaymentForm', 'OrderSummary']},
            ],
            features=['Product catalog', 'Shopping cart', 'Stripe payments', 'Order management'],
            compliance_features=['PCI compliance', 'Refund policy', 'Privacy policy'],
            security_features=['Secure payments', 'PCI-DSS', 'Fraud detection'],
        )

    def _create_blog_platform_template(self) -> AppTemplate:
        """Blogging platform"""
        return AppTemplate(
            id='blog_platform',
            name='Blog Platform',
            category='Content',
            description='Blogging platform with posts, categories, and comments',
            tech_stack={
                'backend': 'Node.js + Express',
                'frontend': 'React',
                'database': 'PostgreSQL',
                'deployment': 'Vercel'
            },
            entities=[
                {'name': 'User', 'fields': [
                    {'name': 'email', 'type': 'email', 'required': True, 'unique': True},
                    {'name': 'password_hash', 'type': 'string', 'required': True},
                    {'name': 'name', 'type': 'string', 'required': True},
                    {'name': 'bio', 'type': 'text'},
                ]},
                {'name': 'Post', 'fields': [
                    {'name': 'author_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                    {'name': 'title', 'type': 'string', 'required': True},
                    {'name': 'content', 'type': 'text', 'required': True},
                    {'name': 'published', 'type': 'boolean', 'default': 'false'},
                    {'name': 'featured_image', 'type': 'url'},
                    {'name': 'slug', 'type': 'string', 'unique': True, 'indexed': True},
                ]},
            ],
            api_endpoints=[
                {'method': 'GET', 'path': '/api/posts', 'description': 'List posts'},
                {'method': 'POST', 'path': '/api/posts', 'description': 'Create post'},
                {'method': 'GET', 'path': '/api/posts/:slug', 'description': 'Get post'},
            ],
            ui_pages=[
                {'name': 'Home', 'route': '/', 'components': ['PostList']},
                {'name': 'Post', 'route': '/post/:slug', 'components': ['PostContent', 'Comments']},
                {'name': 'Editor', 'route': '/editor', 'components': ['MarkdownEditor']},
            ],
            features=['Rich text editor', 'Categories', 'Tags', 'Comments', 'SEO optimization'],
            compliance_features=['Content moderation', 'DMCA compliance'],
            security_features=['XSS protection', 'Content sanitization'],
        )

    def _create_education_platform_template(self) -> AppTemplate:
        """Educational platform with courses and lessons"""
        return AppTemplate(
            id='education_platform',
            name='Education Platform',
            category='Education',
            description='Online learning platform with courses, lessons, and quizzes',
            tech_stack={
                'backend': 'Node.js + Express',
                'frontend': 'React + TypeScript',
                'database': 'PostgreSQL',
                'video': 'Vimeo/YouTube API',
                'deployment': 'AWS'
            },
            entities=[
                {'name': 'User', 'fields': [
                    {'name': 'email', 'type': 'email', 'required': True, 'unique': True},
                    {'name': 'password_hash', 'type': 'string', 'required': True},
                    {'name': 'name', 'type': 'string', 'required': True},
                    {'name': 'role', 'type': 'string', 'default': "'student'"},
                ]},
                {'name': 'Course', 'fields': [
                    {'name': 'instructor_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                    {'name': 'title', 'type': 'string', 'required': True},
                    {'name': 'description', 'type': 'text', 'required': True},
                    {'name': 'price', 'type': 'float'},
                    {'name': 'published', 'type': 'boolean', 'default': 'false'},
                ]},
                {'name': 'Lesson', 'fields': [
                    {'name': 'course_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'courses'}},
                    {'name': 'title', 'type': 'string', 'required': True},
                    {'name': 'content', 'type': 'text', 'required': True},
                    {'name': 'video_url', 'type': 'url'},
                    {'name': 'order', 'type': 'integer', 'default': '0'},
                ]},
                {'name': 'Enrollment', 'fields': [
                    {'name': 'user_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'users'}},
                    {'name': 'course_id', 'type': 'string', 'required': True, 'foreign_key': {'table': 'courses'}},
                    {'name': 'progress', 'type': 'integer', 'default': '0'},
                    {'name': 'completed', 'type': 'boolean', 'default': 'false'},
                ]},
            ],
            api_endpoints=[
                {'method': 'GET', 'path': '/api/courses', 'description': 'List courses'},
                {'method': 'POST', 'path': '/api/courses', 'description': 'Create course'},
                {'method': 'GET', 'path': '/api/courses/:id/lessons', 'description': 'Get course lessons'},
                {'method': 'POST', 'path': '/api/enroll/:courseId', 'description': 'Enroll in course'},
                {'method': 'PUT', 'path': '/api/progress', 'description': 'Update progress'},
            ],
            ui_pages=[
                {'name': 'CourseCatalog', 'route': '/', 'components': ['CourseGrid', 'SearchFilter']},
                {'name': 'CourseDetail', 'route': '/course/:id', 'components': ['CourseInfo', 'LessonList']},
                {'name': 'LessonPlayer', 'route': '/lesson/:id', 'components': ['VideoPlayer', 'LessonContent', 'Quiz']},
                {'name': 'Dashboard', 'route': '/dashboard', 'components': ['EnrolledCourses', 'ProgressTracker']},
            ],
            features=['Course creation', 'Video lessons', 'Progress tracking', 'Certificates', 'Quizzes'],
            compliance_features=['COPPA (if children)', 'Content licensing', 'Accessibility (WCAG)'],
            security_features=['Video DRM', 'Content protection', 'Secure payments'],
        )


# Singleton instance
template_library = TemplateLibrary()
