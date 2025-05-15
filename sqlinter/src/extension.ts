import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';


const execAsync = promisify(exec);


export function activate(context: vscode.ExtensionContext) {
    console.log('Congratulations, your extension "sqlinter" is now active!');

	//обработка сохранения
    const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (document) => {
        if (document.languageId === 'python' || document.fileName.endsWith('.py')) {
			try {
            await runPythonScript(document.fileName);
        } catch (error) {
            vscode.window.showErrorMessage(`Ошибка: ${error}`);
        }
	        vscode.window.showInformationMessage('Сохранение обработано');
            runPythonScript(document.fileName);
        }
    });

    // Добавляем в подписки для очистки при деактивации
    context.subscriptions.push(saveDisposable);

    //базовый хеллоу ворлд
    const disposable = vscode.commands.registerCommand('sqlinter.helloWorld', () => {
		console.log('Hello World from SQLinter!');
        vscode.window.showInformationMessage('Hello World from SQLinter!');
    });
    context.subscriptions.push(disposable);
}

async function runPythonScript(filePath: string) {
    // Получаем путь к директории, где лежит extension.ts
    const extensionDir = path.dirname(__dirname);
    
    // Формируем путь к Python-скрипту в той же директории
    const pythonScriptPath = path.join(extensionDir, 'src/sql_extractor.py');
    
    const command = `python "${pythonScriptPath}" "${filePath}"`;
    
    const { stdout, stderr } = await execAsync(command);
    
    const outputChannel = vscode.window.createOutputChannel('Python Output');
    outputChannel.appendLine(stdout);
    if (stderr) outputChannel.appendLine(`Ошибки: ${stderr}`);
    outputChannel.show();
}

export function deactivate() {}