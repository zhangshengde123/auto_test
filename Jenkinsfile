pipeline {
    agent any
    environment {
        PYTHONIOENCODING = 'UTF-8'
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Install') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Test') {
            steps {
                // 运行并生成 Allure 结果数据
                sh 'python -m pytest --alluredir=reports/allure-results'
            }
        }
    }
    post {
        always {
            // 生成 Allure 报告（需安装 Allure Jenkins 插件）
            allure includeProperties: false, jdk: '', results: [[path: 'reports/allure-results']]
        }
        failure {
            // 可选：在此接入企业微信/钉钉通知，或使用 Jenkins 邮件插件
            echo '测试失败，请查看 Allure 报告'
        }
    }
}
