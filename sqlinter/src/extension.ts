import * as vscode from 'vscode';
import { exec } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    console.log('Congratulations, your extension "sqlinter" is now active!');

    // Регистрируем обработчик для сохранения файла
    const saveDisposable = vscode.workspace.onDidSaveTextDocument((document) => {
        // Проверяем, нужно ли обрабатывать этот файл (например, по расширению)
        if (document.fileName.endsWith('.py')) {  // Можете изменить условие
            runPythonScript(document.fileName);
        }
    });

    // Добавляем в подписки для очистки при деактивации
    context.subscriptions.push(saveDisposable);

    // Ваша существующая команда
    const disposable = vscode.commands.registerCommand('sqlinter.helloWorld', () => {
        vscode.window.showInformationMessage('Hello World from SQLinter!');
    });
    context.subscriptions.push(disposable);
}

function runPythonScript(filePath: string) {
    // Путь к вашему Python-скрипту (может быть абсолютным или относительным)
    const pythonScriptPath = '/path/to/your/script.py';  // ЗАМЕНИТЕ на реальный путь
    
    // Выполняем Python-скрипт
    exec(`python ${pythonScriptPath} "${filePath}"`, (error, stdout, stderr) => {
        if (error) {
            vscode.window.showErrorMessage(`Ошибка выполнения Python-скрипта: ${error.message}`);
            return;
        }
        if (stderr) {
            vscode.window.showWarningMessage(`Предупреждение: ${stderr}`);
        }
        // Выводим результат в output канал
        const outputChannel = vscode.window.createOutputChannel('Python Script Output');
        outputChannel.appendLine(stdout);
        outputChannel.show();
    });
}

export function deactivate() {}