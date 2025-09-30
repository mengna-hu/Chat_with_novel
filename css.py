def design_css():
    custom_css = """
    /* 设置整个页面的背景图片并添加半透明覆盖层 */
    .gradio-container {
        background: url('file=./images/logo_1.png') no-repeat center center fixed;
        background-size: cover;
        min-height: 100vh;
        padding: 20px;
    }

    /* 主要内容区域样式 - 半透明背景提高可读性 */
    .main-content {
        background: rgba(255, 255, 255, 0.6);
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        max-width: 1200px;
        margin: 0 auto;
    }

    /* 标题样式 */
    .title {
        text-align: center;
        color: #2c3e50;
        font-size: 2.5em;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px rgba(255, 255, 255, 0.7);
        font-weight: bold;
    }

    /* 副标题样式 */
    .subtitle {
        text-align: center;
        color: #34495e;
        font-size: 1.2em;
        margin-bottom: 3px;
        font-style: italic;
    }

    #transparent-chatbot {
        background: rgba(255, 255, 255, 0.6) ;
        border: 1px solid rgba(255, 255, 255, 0.3) ;
        overflow-y: auto !important; /* 确保垂直方向可滚动 */
    }

    #transparent-chatbot .message {
        margin: 3px;
        border-radius: 5px;
    }

    /* 按钮透明度效果 */
    #clear {
        background: rgba(0, 0, 0, 0.95) ;
        border: 1px solid rgba(255, 255, 255, 0.3) ;
        color: white ;
        border-radius: 8px ;
        padding: 10px 20px ;
        transition: all 0.3s ease ;
        backdrop-filter: blur(5px) ;
    }

    #clear:hover {
        background: rgba(0, 0, 0, 0.5) ;
        transform: translateY(-2px) ;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3) ;
    }
    
    """
    return custom_css