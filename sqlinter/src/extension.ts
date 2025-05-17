import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';


const execAsync = promisify(exec);


export function activate(context: vscode.ExtensionContext) {
    const extensionRootPath = context.extensionUri.fsPath;
    console.log('Congratulations, your extension "sqlinter" is now active!');
    console.log(extensionRootPath);

	//обработка сохранения
const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (document) => {
    const absoluteFilePath = document.fileName; //абсолютный путь к файлу
    console.log(absoluteFilePath);
    
    if (document.languageId === 'python' || document.fileName.endsWith('.py')) {
        try {
            await runPythonScript(extensionRootPath, absoluteFilePath);
            vscode.window.showInformationMessage(`Обработан файл: ${absoluteFilePath}`);
        } catch (error) {
            vscode.window.showErrorMessage(`Ошибка обработки ${absoluteFilePath}: ${error}`);
        }
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

async function runPythonScript(rootPath: string, filePath: string) {
    // Получаем путь к директории с расширением
    const extensionDir = rootPath;
    
    // Формируем путь к Python-скрипту в той же директории
    const pythonScriptPath = path.join(extensionDir, 'scripts/sql_extractor.py'); 
    console.log(pythonScriptPath);
    const command = `python "${pythonScriptPath}" "${filePath}"`;
    
    const { stdout, stderr } = await execAsync(command);
    
    const outputChannel = vscode.window.createOutputChannel('Python Output');


    outputChannel.appendLine(stdout);
    if (stderr) outputChannel.appendLine(`Ошибки: ${stderr}`);
    outputChannel.show();
}

export function deactivate() {}