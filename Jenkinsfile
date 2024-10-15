pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/ATZ-choosak/HandByHand'
            }
        }
        
        stage('SonarQube Analysis') {
            environment {
                scannerHome = tool 'Sonar' // Ensure 'SonarScanner' is configured in Jenkins
            }
            steps {
                script {
                    withSonarQubeEnv('Sonar') { // Ensure 'SonarQube' is correctly configured in Jenkins
                        sh """
                        ${scannerHome}/bin/sonar-scanner \
                          -Dsonar.projectKey=HandByHand \
                          -Dsonar.sources=. \
                          -Dsonar.host.url=http://192.168.1.45:7070 \
                          -Dsonar.login=sqp_c365c4a98185d283f25463faec65b961b5017b4e
                        """
                    }
                }
            }
        }
    }
}
