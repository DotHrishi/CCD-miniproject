pipeline {
    agent any

    environment {
        REGISTRY = "local"
    }

    stages {
        stage('Checkout Code') {
            steps {
                git 'https://github.com/DotHrishi/CCD-miniproject.git'
            }
        }

        stage('Build Docker Images') {
            steps {
                sh 'docker build -t api-service:latest ./services/api-service'
                sh 'docker build -t auth-service:latest ./services/auth-service'
                sh 'docker build -t storage-service:latest ./services/storage-service'
                sh 'docker build -t frontend:latest ./services/frontend'
            }
        }

        stage('Run Containers') {
            steps {
                sh 'docker compose -f docker-compose.yml up -d'
            }
        }

        stage('Test Health Checks') {
            steps {
                sh 'curl -f http://localhost:5001/health || exit 1'
                sh 'curl -f http://localhost:5002/health || exit 1'
                sh 'curl -f http://localhost:5003/health || exit 1'
            }
        }

        stage('Stop Containers') {
            steps {
                sh 'docker compose down'
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
