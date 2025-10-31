pipeline {
    agent any

    environment {
        REGISTRY = "local"
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/DotHrishi/CCD-miniproject.git'
            }
        }

        stage('Build Docker Images') {
            steps {
                // Use 'bat' for Windows command line instead of 'sh'
                bat 'docker build -t api-service:latest ./services/api-service'
                bat 'docker build -t auth-service:latest ./services/auth-service'
                bat 'docker build -t storage-service:latest ./services/storage-service'
                bat 'docker build -t frontend:latest ./services/frontend'
            }
        }

        stage('Rebuild Without Cache') {
            steps {
        bat 'docker compose -f docker-compose.yml down || exit 0'
        bat 'docker compose -f docker-compose.yml build --no-cache'
            }
        }


        stage('Run Containers') {
            steps {
                bat 'docker compose -f docker-compose.yml up -d'
            }
        }

        stage('Test Health Checks') {
            steps {
                bat '''
                curl -f http://localhost:5001/health || exit /b 1
                curl -f http://localhost:5002/health || exit /b 1
                curl -f http://localhost:5000/health || exit /b 1
                '''
            }
        }

        stage('Stop Containers') {
            steps {
                bat 'docker compose down'
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline executed successfully!'
        }
        failure {
            echo '❌ Pipeline failed. Check logs.'
        }
    }
}
